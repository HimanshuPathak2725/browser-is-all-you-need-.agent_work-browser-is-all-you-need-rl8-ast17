# Compiler-guided CHARM GRPO on GCP

This run is a three-epoch clean-room GRPO pilot. It does not train on the
fixed-26 suite, the r5 public-PR prompt, its reference patch, or private probe.
The exact r5 fmtlib task is used once, after training, as a held-out diagnostic.

## Frozen run contract

- 36 certified gradient tasks and 114 task/prompt-variant groups.
- Short, medium, detailed, and certified repair prompt variants.
- 12 task-disjoint mechanism-monitor tasks and 41 monitor prompt groups.
- 19 prompts per rollout, 8 samples per prompt, and 152 samples per update.
- 18 updates: exactly six updates per corpus epoch for three epochs.
- C++17 `-Wall -Wextra -Werror -pedantic` executable rewards in a separate,
  network-disabled Docker verifier.
- One host-wide lock at `/tmp/glm47-gpu-heavy.lock` for conversion, GRPO, and
  held-out evaluation.

The canonical training topology is eight H100 80GB GPUs with TP4, PP1, EP8,
and ETP1. The held-out evaluator is bound to four A100 80GB GPUs with TP4.
The existing four-A100 evaluation VM can build and verify the images, but it
must refuse conversion and GRPO training.

## Build the deployment bundle

Run from the repository root:

```bash
python3 scripts/package_charm_compiler_grpo_gcp.py \
  --output /tmp/charm-compiler-grpo-gcp-r1.tgz
```

Upload it to a VM:

```bash
gcloud compute scp \
  /tmp/charm-compiler-grpo-gcp-r1.tgz \
  glm47-synthmem-50ep-pr-eval:/tmp/charm-compiler-grpo-gcp-r1.tgz \
  --project=lifeandhalf-24122025 \
  --zone=us-central1-a
```

Extract it on the VM:

```bash
sudo mkdir -p /opt/glm47-public-pr/charm-grpo-r1
sudo chown "${USER}:${USER}" /opt/glm47-public-pr/charm-grpo-r1
tar -xzf /tmp/charm-compiler-grpo-gcp-r1.tgz \
  -C /opt/glm47-public-pr/charm-grpo-r1
cd /opt/glm47-public-pr/charm-grpo-r1
```

## Inspect and prepare

The inventory command is read-only:

```bash
./scripts/gcp_charm_grpo_pipeline.sh inspect
```

Build the isolated verifier, training image, and held-out image and write a
preparation receipt:

```bash
./scripts/gcp_charm_grpo_pipeline.sh prepare
```

On the four-A100 VM this phase is supported. The resulting inventory must say
`grpo_supported: false` and `heldout_eval_supported: true`.

## Reconstruct the warm-start adapter

The warm-start adapter must contain both its complete HF state and a
rank-compatible native TP template. The known 50-epoch asset contains eight
unmerged TP4/EP8 source-native shards, so invoke the explicit source-native
mode. The reconstruction is byte-exact and emits a fresh TP4/EP8 adapter only
after complete template and source round-trip proofs pass.

```bash
./scripts/gcp_charm_grpo_pipeline.sh reconstruct-adapter \
  --native-template /opt/glm47-public-pr/assets/adapter \
  --source-native-template \
  --output-adapter /opt/glm47-public-pr/results/charm-compiler-grpo/reconstructed-start-adapter
```

Do not invent, download, or substitute another native template. The launcher
requires the source-native path to equal the pinned source adapter path and the
reconstructor proves the eight shards against the pinned HF adapter before it
writes output.

## Convert and train on the eight-H100 VM

Copy the bundle, base model, source adapter, and certified native template to
the canonical eight-H100 VM. Run preparation and reconstruction there, then:

```bash
./scripts/gcp_charm_grpo_pipeline.sh convert
```

Start the exact pilot in the foreground:

```bash
./scripts/gcp_charm_grpo_pipeline.sh train \
  --start-adapter /opt/glm47-public-pr/results/charm-compiler-grpo/reconstructed-start-adapter
```

The command refuses non-H100 hardware, a missing TP4/PP1/EP8 checkpoint, an
unproved native adapter, digest drift, a second GPU job, verifier
infrastructure errors, mixed prompt groups, missing reward variance, missing
rollout dumps, or incomplete checkpoint state. A successful run stages only
`adapter_model.bin`, `adapter_config.json`, and a run marker for evaluation.

## Run the held-out twelve-mechanism diagnostic once

Copy the staged `eval-adapter/` and `completion-receipt.json` from the training
VM to the four-A100 evaluation VM. Then run:

```bash
./scripts/gcp_charm_grpo_pipeline.sh eval \
  --eval-adapter /path/to/eval-adapter \
  --completion-receipt /path/to/completion-receipt.json
```

This invokes only the single-task `fmtlib-demo` suite. The evaluation image
verifies the unchanged r5 JSONL digest, oracle preparation receipts, all base
model files, the exact post-GRPO adapter hashes, network isolation, and the
four-A100 inventory before inference.

## Concurrency

Do not run GRPO, checkpoint conversion, or evaluation simultaneously on one
VM. Both the 8-H100 trainer and 4-A100 evaluator consume their full GPU
topology. CPU-only bundle and image preparation can overlap. To run multiple
GPU-heavy jobs concurrently, use separate VMs and independent result roots.
