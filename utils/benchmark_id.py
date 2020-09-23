""""
Module for handling CommonRoad Benchmark ID
"""
__author__ = "Peter Kocsis"
__copyright__ = "TUM Cyber-Physical System Group"
__credits__ = []
__version__ = "0.1"
__maintainer__ = "Moritz Klischat"
__email__ = "moritz.klischat@tum.de"
__status__ = "Integration"

import os
from typing import List


class CRBenchmarkID:
    """
    Class for creating and splitting benchmark ids
    """

    def __init__(self, country: str, scene: str, config: str, pred: str):
        """
        Initialize new object
        :param country: The country of the scenario
        :param scene: The scene of the scenario
        :param config: The config of the scenario
        :param pred: The type of the prediction of the scenario
        """
        self.country, self.scene, self.config, self.pred = country, scene, config, pred
        self.benchmark_id = self._build_benchmark_id()

    def _build_benchmark_id(self) -> str:
        """
        Build benchmark ID from the object
        :return The benchmark ID as string
        """
        return '_'.join([self.country, self.scene, self.config, self.pred])

    @classmethod
    def from_string(cls, benchmark_id: str) -> 'CRBenchmarkID':
        """
        Create object from full benchmark ID string
        :param benchmark_id: The benchmark ID as string
        :return The benchmark ID as object
        """
        country, scene, config, pred = cls._split_benchmark_id(benchmark_id)
        return cls(country, scene, config, pred)

    @classmethod
    def from_path(cls, senario_path: str) -> 'CRBenchmarkID':
        """
        Create object from path of scenario
        :param senario_path: The path of the scenario file
        :retun The benchmark ID as object
        """
        benchmark_id = os.path.splitext(os.path.basename(senario_path))[0]
        return cls.from_string(benchmark_id)

    @staticmethod
    def _split_benchmark_id(benchmark_id: str) -> List[str]:
        """
        Split benchmark id
        :param benchmark_id: The benchmark ID as string to be split
        :return List of strings containing the split values of the benchmark ID
        """
        split_benchmark_id = benchmark_id.split('_')
        if len(split_benchmark_id) != 4:
            raise ValueError(f"Invalid benchmark ID: {benchmark_id}")
        return split_benchmark_id

    def __str__(self) -> str:
        """String value of the benchmark ID"""
        return self.benchmark_id

    def __repr__(self) -> str:
        """The representation of the object"""
        return self.benchmark_id
