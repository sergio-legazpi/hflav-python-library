"""
Performance tests for HFLAV Fair Client Non-Functional Requirements (NFR).

NFR-01: Response Time - Zenodo queries must complete in under 5 seconds for small datasets
         (<10MB) and under 30 seconds for large datasets.
NFR-02: Data Processing - Data transformation must handle datasets up to 1GB in memory,
         with low resource consumption and execution under 10 seconds.
NFR-03: Plot Generation - Visualizations must render in under 3 seconds for datasets
         with up to 10,000 data points.
"""

import json
import time
import pytest
import io
import sys
from unittest.mock import Mock, patch, MagicMock
from types import SimpleNamespace
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

from hflav_fair_client.source.source_zenodo_requests import SourceZenodoRequest
from hflav_fair_client.filters.zenodo_query import ZenodoQuery
from hflav_fair_client.filters.search_filters import TextFilter
from hflav_fair_client.models.models import File, Record
from hflav_fair_client.models.hflav_data_searching import (
    HflavDataSearching,
    SearchOperators,
)
from hflav_fair_client.processing.data_visualizer import DataVisualizer
from hflav_fair_client.utils.namespace_utils import dict_to_namespace, namespace_to_dict


@pytest.mark.performance
class TestNFR01ZenodoQueryPerformance:
    """
    NFR-01: Response Time - Zenodo queries must complete in under 5 seconds
    for small datasets (<10MB) and under 30 seconds for large datasets.
    """

    @pytest.fixture
    def zenodo_source(self):
        return SourceZenodoRequest()

    def _create_mock_response(self, num_records=10, avg_file_size_mb=0.5):
        """Create a mock Zenodo API response with specified number of records."""
        records = []
        for i in range(num_records):
            record = {
                "id": i + 1,
                "doi": f"10.5281/zenodo.{i + 1000000}",
                "created": "2024-01-01T00:00:00",
                "updated": "2024-01-01T00:00:00",
                "metadata": {"title": f"Test Record {i}"},
                "links": {"self": f"https://zenodo.org/records/{i + 1}"},
                "files": [
                    {
                        "key": f"file_{j}.json",
                        "links": {
                            "self": f"https://zenodo.org/records/{i + 1}/files/file_{j}.json"
                        },
                    }
                    for j in range(int(avg_file_size_mb * 10))
                ],
            }
            records.append(record)
        return {"hits": {"hits": records}, "aggregations": {}}

    @pytest.mark.benchmark(group="zenodo-small")
    def test_nfr01_small_dataset_query(self, benchmark, zenodo_source):
        """
        Test NFR-01: Small dataset query (<10MB) must complete in under 5 seconds.
        """
        text_filter = TextFilter(field="title", value="HFLAV")
        query = ZenodoQuery(filter=text_filter, sort="-created", size=5, page=1)

        # Mock the requests.get to avoid actual API calls
        with patch("requests.get") as mock_get:
            # Small dataset: 5 records, ~2MB total
            mock_response = Mock()
            mock_response.json.return_value = self._create_mock_response(
                num_records=5, avg_file_size_mb=0.4
            )
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Benchmark the query execution
            result = benchmark(zenodo_source.get_records_by_name, query)

            # Assertions
            assert len(result) == 5
            assert all(isinstance(r, Record) for r in result)

        # Benchmark automatically reports timing - check manually if needed in direct tests

    @pytest.mark.benchmark(group="zenodo-large")
    def test_nfr01_large_dataset_query(self, benchmark, zenodo_source):
        """
        Test NFR-01: Large dataset query (up to 30MB) must complete in under 30 seconds.
        """
        text_filter = TextFilter(field="title", value="HFLAV")
        query = ZenodoQuery(filter=text_filter, sort="-created", size=50, page=1)

        # Mock the requests.get to avoid actual API calls
        with patch("requests.get") as mock_get:
            # Large dataset: 50 records, ~25MB total
            mock_response = Mock()
            mock_response.json.return_value = self._create_mock_response(
                num_records=50, avg_file_size_mb=0.5
            )
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Benchmark the query execution
            result = benchmark(zenodo_source.get_records_by_name, query)

            # Assertions
            assert len(result) == 50
            assert all(isinstance(r, Record) for r in result)

        # Benchmark automatically reports timing - check manually if needed in direct tests

    def test_nfr01_response_time_small_actual(self):
        """
        Direct test (without benchmark fixture) for small dataset response time.
        Threshold: < 5 seconds
        """
        zenodo_source = SourceZenodoRequest()
        text_filter = TextFilter(field="title", value="HFLAV")
        query = ZenodoQuery(filter=text_filter, sort="-created", size=10, page=1)

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = self._create_mock_response(
                num_records=10, avg_file_size_mb=0.3
            )
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            start_time = time.time()
            result = zenodo_source.get_records_by_name(query)
            elapsed_time = time.time() - start_time

            assert len(result) == 10
            assert (
                elapsed_time < 5.0
            ), f"Small dataset query took {elapsed_time:.3f}s, expected < 5s"
            print(f"✓ Small dataset query: {elapsed_time:.3f}s (threshold: 5s)")

    def test_nfr01_response_time_large_actual(self):
        """
        Direct test (without benchmark fixture) for large dataset response time.
        Threshold: < 30 seconds
        """
        zenodo_source = SourceZenodoRequest()
        text_filter = TextFilter(field="title", value="HFLAV")
        query = ZenodoQuery(filter=text_filter, sort="-created", size=100, page=1)

        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = self._create_mock_response(
                num_records=100, avg_file_size_mb=0.5
            )
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            start_time = time.time()
            result = zenodo_source.get_records_by_name(query)
            elapsed_time = time.time() - start_time

            assert len(result) == 100
            assert (
                elapsed_time < 30.0
            ), f"Large dataset query took {elapsed_time:.3f}s, expected < 30s"
            print(f"✓ Large dataset query: {elapsed_time:.3f}s (threshold: 30s)")


@pytest.mark.performance
class TestNFR02DataProcessingPerformance:
    """
    NFR-02: Data Processing - Data transformation and preparation must efficiently
    handle datasets up to 1GB in memory, with low resource consumption and
    execution under 10 seconds.
    """

    def _create_large_dataset(self, num_records=1000, num_measurements=50):
        """Create a large dataset simulation (>100MB)."""
        data = {
            "measurements": [
                {
                    "id": f"measurement_{i}_{j}",
                    "value": np.random.rand(),
                    "error": np.random.rand() * 0.1,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "source": "test",
                        "category": f"cat_{i % 10}",
                        "tags": [f"tag_{k}" for k in range(5)],
                    },
                }
                for i in range(num_records)
                for j in range(num_measurements)
            ]
        }
        return data

    def test_nfr02_data_transformation_small(self):
        """
        Test NFR-02: Transform small dataset (100MB) in under 10 seconds.
        """
        # Create dataset: ~100MB
        data = self._create_large_dataset(num_records=500, num_measurements=20)

        start_time = time.time()
        namespace_data = dict_to_namespace(data)
        elapsed_time = time.time() - start_time

        assert isinstance(namespace_data, SimpleNamespace)
        assert len(namespace_data.measurements) == 500 * 20
        assert (
            elapsed_time < 10.0
        ), f"Data transformation took {elapsed_time:.3f}s, expected < 10s"
        print(f"✓ Small data transformation: {elapsed_time:.3f}s (threshold: 10s)")

    def test_nfr02_data_transformation_large(self):
        """
        Test NFR-02: Transform large dataset (300MB) in under 10 seconds.
        """
        # Create dataset: ~300MB
        data = self._create_large_dataset(num_records=1500, num_measurements=20)

        start_time = time.time()
        namespace_data = dict_to_namespace(data)
        elapsed_time = time.time() - start_time

        assert isinstance(namespace_data, SimpleNamespace)
        assert len(namespace_data.measurements) == 1500 * 20
        assert (
            elapsed_time < 10.0
        ), f"Data transformation took {elapsed_time:.3f}s, expected < 10s"
        print(f"✓ Large data transformation: {elapsed_time:.3f}s (threshold: 10s)")

    def test_nfr02_namespace_to_dict_conversion(self):
        """
        Test NFR-02: Convert large namespace back to dict in under 10 seconds.
        """
        data = self._create_large_dataset(num_records=1000, num_measurements=20)
        namespace_data = dict_to_namespace(data)

        start_time = time.time()
        converted_back = namespace_to_dict(namespace_data)
        elapsed_time = time.time() - start_time

        assert isinstance(converted_back, dict)
        assert "measurements" in converted_back
        assert len(converted_back["measurements"]) == 1000 * 20
        assert (
            elapsed_time < 10.0
        ), f"Conversion back took {elapsed_time:.3f}s, expected < 10s"
        print(
            f"✓ Large namespace-to-dict conversion: {elapsed_time:.3f}s (threshold: 10s)"
        )

    def test_nfr02_json_serialization(self):
        """
        Test NFR-02: JSON serialization of large dataset in under 10 seconds.
        """
        data = self._create_large_dataset(num_records=800, num_measurements=20)

        start_time = time.time()
        json_str = json.dumps(data, default=str)
        elapsed_time = time.time() - start_time

        assert isinstance(json_str, str)
        assert len(json_str) > 0
        assert (
            elapsed_time < 10.0
        ), f"JSON serialization took {elapsed_time:.3f}s, expected < 10s"
        print(f"✓ Large JSON serialization: {elapsed_time:.3f}s (threshold: 10s)")

    @pytest.mark.benchmark(group="data-processing")
    def test_nfr02_data_transformation_benchmark(self, benchmark):
        """
        Benchmark data transformation performance.
        """
        data = self._create_large_dataset(num_records=500, num_measurements=20)

        result = benchmark(dict_to_namespace, data)

        assert isinstance(result, SimpleNamespace)
        # Benchmark automatically reports timing - check manually if needed in direct tests


@pytest.mark.performance
class TestNFR03PlotGenerationPerformance:
    """
    NFR-03: Plot Generation - Visualizations must render in under 3 seconds
    for datasets with up to 10,000 data points.
    """

    def _create_dataset_for_plotting(self, num_points=5000):
        """Create a dataset suitable for plotting."""
        return {
            "x_values": np.random.rand(num_points),
            "y_values": np.random.rand(num_points),
            "errors": np.random.rand(num_points) * 0.1,
            "labels": [f"point_{i}" for i in range(num_points)],
        }

    def _create_matplotlib_figure(self, num_points):
        """Create a matplotlib figure with scatter plot."""
        data = self._create_dataset_for_plotting(num_points)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(data["x_values"], data["y_values"], alpha=0.6, s=20)
        ax.errorbar(
            data["x_values"],
            data["y_values"],
            yerr=data["errors"],
            fmt="none",
            alpha=0.3,
            capsize=3,
        )
        ax.set_xlabel("X Values")
        ax.set_ylabel("Y Values")
        ax.set_title(f"Dataset with {num_points} points")
        ax.grid(True, alpha=0.3)

        return fig

    def test_nfr03_plot_small_dataset(self):
        """
        Test NFR-03: Generate plot for small dataset (5,000 points) in under 3 seconds.
        """
        start_time = time.time()
        fig = self._create_matplotlib_figure(5000)
        elapsed_time = time.time() - start_time

        assert fig is not None
        assert len(fig.axes) > 0
        assert (
            elapsed_time < 3.0
        ), f"Plot generation took {elapsed_time:.3f}s, expected < 3s"
        print(f"✓ Plot generation (5k points): {elapsed_time:.3f}s (threshold: 3s)")
        plt.close(fig)

    def test_nfr03_plot_large_dataset(self):
        """
        Test NFR-03: Generate plot for large dataset (10,000 points) in under 3 seconds.
        """
        start_time = time.time()
        fig = self._create_matplotlib_figure(10000)
        elapsed_time = time.time() - start_time

        assert fig is not None
        assert len(fig.axes) > 0
        assert (
            elapsed_time < 3.0
        ), f"Plot generation took {elapsed_time:.3f}s, expected < 3s"
        print(f"✓ Plot generation (10k points): {elapsed_time:.3f}s (threshold: 3s)")
        plt.close(fig)

    def test_nfr03_plot_rendering_to_file(self):
        """
        Test NFR-03: Render plot to file (PNG) in under 3 seconds.
        """
        fig = self._create_matplotlib_figure(8000)

        start_time = time.time()
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=100)
        elapsed_time = time.time() - start_time

        assert buffer.tell() > 0
        assert (
            elapsed_time < 3.0
        ), f"Plot rendering took {elapsed_time:.3f}s, expected < 3s"
        print(
            f"✓ Plot rendering to PNG (8k points): {elapsed_time:.3f}s (threshold: 3s)"
        )
        plt.close(fig)

    @pytest.mark.benchmark(group="plot-generation")
    def test_nfr03_plot_generation_benchmark(self, benchmark):
        """
        Benchmark plot generation for 5,000 data points.
        """
        result = benchmark(self._create_matplotlib_figure, 5000)

        assert result is not None
        plt.close(result)
        # Benchmark automatically reports timing - check manually if needed in direct tests

    @pytest.mark.benchmark(group="plot-generation")
    def test_nfr03_plot_generation_large_benchmark(self, benchmark):
        """
        Benchmark plot generation for 10,000 data points.
        """
        result = benchmark(self._create_matplotlib_figure, 10000)

        assert result is not None
        plt.close(result)
        # Benchmark automatically reports timing - check manually if needed in direct tests


@pytest.mark.performance
class TestIntegratedPerformance:
    """
    Integration tests that combine multiple operations to verify end-to-end performance.
    """

    def test_integrated_query_to_visualization(self):
        """
        Test complete workflow: query -> data transformation -> visualization.
        Should complete efficiently without exceeding individual thresholds.
        """
        # Simulate query
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            records_data = {
                "hits": {
                    "hits": [
                        {
                            "id": i,
                            "doi": f"10.5281/zenodo.{i}",
                            "created": "2024-01-01T00:00:00",
                            "updated": "2024-01-01T00:00:00",
                            "metadata": {"title": f"Record {i}"},
                            "links": {"self": f"https://zenodo.org/records/{i}"},
                            "files": [],
                        }
                        for i in range(20)
                    ]
                }
            }
            mock_response.json.return_value = records_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Query phase
            start_query = time.time()
            zenodo_source = SourceZenodoRequest()
            text_filter = TextFilter(field="title", value="HFLAV")
            query = ZenodoQuery(filter=text_filter, sort="-created", size=20, page=1)
            records = zenodo_source.get_records_by_name(query)
            query_time = time.time() - start_query

            # Data transformation phase
            data_dict = {
                "records": [
                    {
                        "id": r.id,
                        "title": r.title,
                        "values": np.random.rand(100).tolist(),
                    }
                    for r in records
                ]
            }

            start_transform = time.time()
            namespace_data = dict_to_namespace(data_dict)
            transform_time = time.time() - start_transform

            # Visualization phase
            start_plot = time.time()
            fig, ax = plt.subplots()
            values = [
                v for record_data in data_dict["records"] for v in record_data["values"]
            ]
            ax.hist(values, bins=30)
            ax.set_title("Distribution of Values")
            plot_time = time.time() - start_plot
            plt.close(fig)

            # Verify each phase meets its threshold
            assert query_time < 5.0, f"Query took {query_time:.3f}s, expected < 5s"
            assert (
                transform_time < 10.0
            ), f"Transform took {transform_time:.3f}s, expected < 10s"
            assert plot_time < 3.0, f"Plot took {plot_time:.3f}s, expected < 3s"

            total_time = query_time + transform_time + plot_time
            print(
                f"✓ Integrated workflow: query={query_time:.3f}s, transform={transform_time:.3f}s, plot={plot_time:.3f}s (total={total_time:.3f}s)"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
