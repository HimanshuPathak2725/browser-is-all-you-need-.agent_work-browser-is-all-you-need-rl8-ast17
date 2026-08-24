from strange_cpp import Contract


CONTRACT = Contract(
    task_id="diamond",
    prefix="DMF",
    source_files=("diamond.h", "diamond.cpp"),
    implementation_files=("diamond.cpp",),
    fixed_hashes={
        ".docs/instructions.md": "ff20bbc2d91cf1ffb8b35ffbe4715867a8e0fdec29a83bf8d9ef8a18da2d9d68",
        ".meta/config.json": "ab687c7bd48e4c78c4ebc23650a79d7a876c0562ca8163875ea99cb143fe6b5c",
        ".meta/tests.toml": "2b9c8ee60ab2b86ac7ba50cee1f39727d4a8fab13e1a5f794452670562c9ed8c",
        ".meta/example.h": "360626ddf0588922635755db8aaeaaf4b656679ae85611a3fef19d27f0a4c33b",
        ".meta/example.cpp": "a18f55e3cadb350cb40fe870f18399c5a6c128556cfa68f5f7833f938ce1ce6f",
        "CMakeLists.txt": "53d531120e650972adf19a2a42aa2d5bc716c93700ffac74c1c2868fdce633ff",
        "test/catch.hpp": "681e7505a50887c9085539e5135794fc8f66d8e5de28eadf13a30978627b0f47",
        "test/tests-main.cpp": "5847fda35c1320d94f8d088aaf34229d689f66f1da235f885cbb28c8f17e4260",
        "diamond_test.cpp": "235fc2baac052df9b1efd981d93924b37a738dc85e5b056547a78eeb8840da3f",
    },
    test_file="diamond_test.cpp",
)
