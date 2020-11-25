import pytest
import os
import pathpy
import subprocess
from .context import src


@pytest.mark.parametrize(
    "test_syscall, parsed_syscall",
    [
        (
            "1340 21:09:45.230382300 6 101 nginx 16840 > epoll_wait maxevents=512",
            [
                "1340",
                "21:09:45.230382300",
                "6",
                "101",
                "nginx",
                "16840",
                ">",
                "epoll_wait",
                ["maxevents=512"],
            ],
        ),
        (
            "446 21:09:43.368862035 6 101 nginx 16840 > recvfrom fd=13(<4t>172.17.0.1:44548->172.17.0.3:8080) size=1024",
            [
                "446",
                "21:09:43.368862035",
                "6",
                "101",
                "nginx",
                "16840",
                ">",
                "recvfrom",
                ["fd=13(<4t>172.17.0.1:44548->172.17.0.3:8080)", "size=1024"],
            ],
        ),
    ],
)
def test_parse_syscall(test_syscall, parsed_syscall):

    result = src.data_processing.parse_syscall(test_syscall)

    assert parsed_syscall[0] == result[0]
    assert parsed_syscall[1] == result[1]
    assert parsed_syscall[2] == result[2]
    assert parsed_syscall[3] == result[3]
    assert parsed_syscall[4] == result[4]
    assert parsed_syscall[5] == result[5]
    assert parsed_syscall[6] == result[6]
    assert parsed_syscall[7] == result[7]
    assert parsed_syscall[8] == result[8]


@pytest.mark.parametrize("run_file, parsed_results", [("test/mock_run.txt", [0, 22467, "futex"])])
def test_parse_run_to_pandas(run_file, parsed_results):

    data = src.data_processing.parse_run_to_pandas(run_file)

    assert data["time"].iloc[0] == parsed_results[0]
    assert data["thread_id"].iloc[0] == parsed_results[1]
    assert data["syscall"].iloc[0] == parsed_results[2]


@pytest.mark.parametrize(
    "run_file, start_end_time, output_paths",
    [
        ("test/mock_run.txt", None, [("futex",)]),
        (
            "test/mock_run_2.txt",
            None,
            [
                ("futex", "futex"),
                ("futex", "futex"),
                ("futex", "futex"),
                ("select", "sched_yield"),
                (
                    "poll",
                    "fcntl",
                    "fcntl",
                    "accept",
                    "fcntl",
                    "getsockname",
                    "fcntl",
                    "fcntl",
                    "setsockopt",
                    "setsockopt",
                    "fcntl",
                    "setsockopt",
                    "setsockopt",
                    "mmap",
                    "mprotect",
                ),
            ],
        ),
        (
            "test/mock_run_2.txt",
            (200000, 500000),
            [("futex", "futex"), ("select", "sched_yield"), ("futex", "futex")],
        ),
    ],
)
def test_generate_paths_from_threads(run_file, start_end_time, output_paths):
    paths = src.data_processing.generate_paths_from_threads(
        src.data_processing.parse_run_to_pandas(run_file), start_end_time
    )

    assert len(output_paths) == paths.observation_count

    for test_path in output_paths:
        assert test_path in paths.paths[len(test_path) - 1]


@pytest.mark.skip(reason="Full test only when manual trigger. Takes long.")
def test_full_pipeline():
    "Testing the full project pipeline with a minimal working example."
    subprocess.call(
        [
            "python",
            "run.py",
            "-u",
            "with",
            "stages.pull_data=True",
            "stages.make_temp_paths=True",
            "stages.create_model=True",
            "model.train_examples=10",
            "simulate.normal_samples=3",
            "simulate.attack_samples=3",
        ]
    )
    assert True
