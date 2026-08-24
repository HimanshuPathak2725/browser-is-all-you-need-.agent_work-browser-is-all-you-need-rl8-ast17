from strange_cpp import Contract


CONTRACT = Contract(
    task_id="kindergarten-garden",
    prefix="KGF",
    source_files=("kindergarten_garden.h", "kindergarten_garden.cpp"),
    implementation_files=("kindergarten_garden.cpp",),
    fixed_hashes={
        ".docs/instructions.md": "0deebfb40706725b72884a95230b3f3a84ed8a16652eb0fdd405ce5516ceacbc",
        ".meta/config.json": "aed2134a9acc7de6d861817dac88674810c86a420f472ba598102265b8c81001",
        ".meta/tests.toml": "7e041e899474b82d176e396b331411a60b89a67d6a31bafbba806ef634971120",
        ".meta/example.h": "f30b9955665b9afb4f8b629cc05192e15e8463e0bd077881171372fe3b2c24d3",
        ".meta/example.cpp": "6e405212f26721c059451557d8fdd4c402427db0fd98966f131815a1439f1264",
        "CMakeLists.txt": "53d531120e650972adf19a2a42aa2d5bc716c93700ffac74c1c2868fdce633ff",
        "test/catch.hpp": "681e7505a50887c9085539e5135794fc8f66d8e5de28eadf13a30978627b0f47",
        "test/tests-main.cpp": "5847fda35c1320d94f8d088aaf34229d689f66f1da235f885cbb28c8f17e4260",
        "kindergarten_garden_test.cpp": "1a35fe4528cf3577739c95df36daafac894e5e554cf51481ebf8c475f683bcfd",
    },
    test_file="kindergarten_garden_test.cpp",
)
