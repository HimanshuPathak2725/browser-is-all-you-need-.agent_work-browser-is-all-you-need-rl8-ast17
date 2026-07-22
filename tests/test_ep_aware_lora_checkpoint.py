from __future__ import annotations

import types
import pickle
from pathlib import Path

import pytest

from glm47_posttraining.integrations import miles_glm47_bridge


class _Tensor:
    shape = (1,)
    dtype = "float32"
    device = "cpu"

    def __init__(self, value: float):
        self.value = float(value)

    @property
    def data(self):
        return self

    def cpu(self):
        return self

    def to(self, *, device):
        assert device == self.device
        return self

    def copy_(self, other) -> None:
        self.value = other.value

    def item(self) -> float:
        return self.value


class _FakeTorch:
    @staticmethod
    def is_tensor(value) -> bool:
        return isinstance(value, _Tensor)

    @staticmethod
    def save(value, path) -> None:
        with Path(path).open("wb") as handle:
            pickle.dump(value, handle)

    @staticmethod
    def load(path, *, map_location, weights_only):
        assert map_location == "cpu"
        assert weights_only is True
        with Path(path).open("rb") as handle:
            return pickle.load(handle)


fake_torch = _FakeTorch()


class _Group:
    def __init__(self, rank: int, size: int):
        self.rank = rank
        self.size = size


class _ParallelState:
    def __init__(
        self,
        *,
        tp_rank: int,
        tp_size: int,
        pp_rank: int,
        pp_size: int,
        ep_rank: int,
        ep_size: int,
        etp_rank: int,
        etp_size: int,
    ):
        self.tp = _Group(tp_rank, tp_size)
        self.pp = _Group(pp_rank, pp_size)
        self.ep = _Group(ep_rank, ep_size)
        self.etp = _Group(etp_rank, etp_size)


class _FakeDist:
    def __init__(self, rank: int, records: list[tuple[int, int, int, int, int]]):
        self.rank = rank
        self.records = records
        self.barriers = 0

    @staticmethod
    def is_available() -> bool:
        return True

    @staticmethod
    def is_initialized() -> bool:
        return True

    def get_rank(self) -> int:
        return self.rank

    def get_world_size(self) -> int:
        return len(self.records)

    def all_gather_object(self, output, local_record) -> None:
        assert local_record == self.records[self.rank]
        output[:] = self.records

    def barrier(self) -> None:
        self.barriers += 1


class _ModelChunk:
    def __init__(self, value: float = 0.0):
        self.adapter = _Tensor(value)

    def named_parameters(self):
        return [("module.adapter.linear_in.weight", self.adapter)]


class _Logger:
    def __init__(self):
        self.messages = []

    def info(self, *args) -> None:
        self.messages.append(args)


def _ep8_records() -> list[tuple[int, int, int, int, int]]:
    # Actual continuation topology: TP=4, PP=1, EP=8, ETP=1.
    return [(rank, rank % 4, 0, rank, 0) for rank in range(8)]


def _state_for_record(record, *, ep_size: int = 8, etp_size: int = 1):
    _, tp, pp, ep, etp = record
    return _ParallelState(
        tp_rank=tp,
        tp_size=4,
        pp_rank=pp,
        pp_size=1,
        ep_rank=ep,
        ep_size=ep_size,
        etp_rank=etp,
        etp_size=etp_size,
    )


def _write_complete_ep8_adapter(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for _, tp, pp, ep, _ in _ep8_records():
        fake_torch.save(
            {"module.adapter.linear_in.weight": _Tensor(ep)},
            path / miles_glm47_bridge._ep_native_adapter_name(tp, pp, ep),
        )


def _fake_lora_module(*, state, dist, legacy_load, legacy_save=None, iteration=17):
    logger = _Logger()

    def load_training_state(adapter_dir, optimizer, opt_param_scheduler):
        assert Path(adapter_dir).is_dir()
        return iteration

    return types.SimpleNamespace(
        load_lora_adapter=legacy_load,
        save_lora_checkpoint=legacy_save,
        get_parallel_state=lambda: state,
        dist=dist,
        torch=fake_torch,
        logger=logger,
        _is_adapter_param_name=lambda name: ".adapter." in name,
        _load_training_state=load_training_state,
    )


def test_ep8_load_selects_exact_tp_pp_ep_shard_and_reloads_optimizer(tmp_path: Path) -> None:
    records = _ep8_records()
    rank = 5
    state = _state_for_record(records[rank])
    dist = _FakeDist(rank, records)
    _write_complete_ep8_adapter(tmp_path)

    def legacy_load(*args, **kwargs):
        raise AssertionError("EP>1 must not use the legacy TP-only loader")

    module = _fake_lora_module(state=state, dist=dist, legacy_load=legacy_load)
    miles_glm47_bridge._apply_warm_start_optimizer_reload(module)
    model = [_ModelChunk()]
    reloads = []
    optimizer = types.SimpleNamespace(reload_model_params=lambda: reloads.append(True))

    loaded, iteration = module.load_lora_adapter(model, tmp_path, optimizer=optimizer)

    assert (loaded, iteration) == (True, 17)
    assert model[0].adapter.item() == 5.0
    assert reloads == [True]
    assert module.logger.messages[-1][2].name == "adapter_megatron_tp1_pp0_ep5.pt"


@pytest.mark.parametrize("present_ep_ranks", [[], [0, 1, 2]])
def test_ep8_load_fails_closed_without_complete_ep_set(
    tmp_path: Path,
    present_ep_ranks: list[int],
) -> None:
    records = _ep8_records()
    rank = 5
    state = _state_for_record(records[rank])
    dist = _FakeDist(rank, records)
    for _, tp, pp, ep, _ in records:
        if ep in present_ep_ranks:
            fake_torch.save(
                {"module.adapter.linear_in.weight": _Tensor(ep)},
                tmp_path / miles_glm47_bridge._ep_native_adapter_name(tp, pp, ep),
            )
    fake_torch.save(
        {"module.adapter.linear_in.weight": _Tensor(-1)},
        tmp_path / "adapter_megatron_tp1_pp0.pt",
    )
    legacy_calls = []

    def legacy_load(*args, **kwargs):
        legacy_calls.append(True)
        return True, 0

    module = _fake_lora_module(state=state, dist=dist, legacy_load=legacy_load)
    miles_glm47_bridge._apply_warm_start_optimizer_reload(module)

    with pytest.raises(RuntimeError, match="refusing TP-only fallback"):
        module.load_lora_adapter([_ModelChunk()], tmp_path)
    assert legacy_calls == []


def test_ep1_preserves_legacy_loader_and_optimizer_reload(tmp_path: Path) -> None:
    records = [(0, 0, 0, 0, 0)]
    state = _state_for_record(records[0], ep_size=1)
    dist = _FakeDist(0, records)
    legacy_calls = []

    def legacy_load(model, adapter_path, *, optimizer=None, opt_param_scheduler=None):
        legacy_calls.append(Path(adapter_path))
        return True, 9

    module = _fake_lora_module(state=state, dist=dist, legacy_load=legacy_load)
    miles_glm47_bridge._apply_warm_start_optimizer_reload(module)
    reloads = []
    optimizer = types.SimpleNamespace(reload_model_params=lambda: reloads.append(True))

    assert module.load_lora_adapter([], tmp_path, optimizer=optimizer) == (True, 9)
    assert legacy_calls == [tmp_path]
    assert reloads == [True]


def test_ep8_save_emits_complete_owner_set_and_removes_legacy_files(
    tmp_path: Path,
    monkeypatch,
) -> None:
    records = _ep8_records()
    rank = 0
    state = _state_for_record(records[rank])
    dist = _FakeDist(rank, records)
    tmp_path.mkdir(parents=True, exist_ok=True)
    for _, tp, pp, ep, _ in records[1:]:
        fake_torch.save(
            {"module.adapter.linear_in.weight": _Tensor(ep)},
            tmp_path / miles_glm47_bridge._ep_native_adapter_name(tp, pp, ep),
        )

    def legacy_load(*args, **kwargs):
        return False, None

    def legacy_save(
        model,
        args,
        save_dir,
        *,
        optimizer=None,
        opt_param_scheduler=None,
        iteration=None,
    ):
        fake_torch.save(
            {"module.adapter.linear_in.weight": _Tensor(-1)},
            Path(save_dir) / "adapter_megatron_tp0_pp0.pt",
        )
        return str(save_dir)

    module = _fake_lora_module(
        state=state,
        dist=dist,
        legacy_load=legacy_load,
        legacy_save=legacy_save,
    )
    monkeypatch.setattr(miles_glm47_bridge.os, "sync", lambda: None)
    miles_glm47_bridge._apply_warm_start_optimizer_reload(module)

    result = module.save_lora_checkpoint([_ModelChunk(42.0)], object(), tmp_path)

    assert result == str(tmp_path)
    assert miles_glm47_bridge._present_ep_native_names(tmp_path) == {
        miles_glm47_bridge._ep_native_adapter_name(tp, pp, ep)
        for _, tp, pp, ep, _ in records
    }
    assert not (tmp_path / "adapter_megatron_tp0_pp0.pt").exists()
    saved = fake_torch.load(
        tmp_path / "adapter_megatron_tp0_pp0_ep0.pt",
        map_location="cpu",
        weights_only=True,
    )
    assert saved["module.adapter.linear_in.weight"].item() == 42.0
    assert dist.barriers == 2


def test_owner_election_deduplicates_dp_replicas() -> None:
    # TP=4, EP=2, ETP=1 has two global-rank replicas for each (TP, PP, EP).
    records = [
        (rank, rank % 4, 0, rank % 2, 0)
        for rank in range(8)
    ]
    rank = 4
    topology = miles_glm47_bridge._ep_native_owner_topology(
        _state_for_record(records[rank], ep_size=2),
        _FakeDist(rank, records),
    )

    assert topology["is_writer"] is False
    assert topology["local_name"] == "adapter_megatron_tp0_pp0_ep0.pt"
    assert topology["expected_names"] == {
        "adapter_megatron_tp0_pp0_ep0.pt",
        "adapter_megatron_tp1_pp0_ep1.pt",
        "adapter_megatron_tp2_pp0_ep0.pt",
        "adapter_megatron_tp3_pp0_ep1.pt",
    }


def test_owner_election_rejects_unrepresentable_etp_collision() -> None:
    records = [(0, 0, 0, 0, 0), (1, 0, 0, 0, 1)]
    state = _state_for_record(records[0], ep_size=2, etp_size=2)

    with pytest.raises(RuntimeError, match="filename collision"):
        miles_glm47_bridge._ep_native_owner_topology(state, _FakeDist(0, records))
