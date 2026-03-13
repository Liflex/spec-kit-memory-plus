"""
Auto-Detection Priority Profiles

Automatically detects the appropriate priority profile based on project files.
Supports detection from package.json, requirements.txt, pyproject.toml, go.mod, and more.
"""

import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any


# Detection patterns for each profile
DETECTION_PATTERNS = {
    "mobile-app": {
        "package_json": {
            "dependencies": [
                "react-native",
                "expo",
                "@react-navigation",
                "react-native-ios",
                "react-native-android",
                "cordova",
                "capacitor",
                "ionic",
                "flutter",
            ],
            "devDependencies": [
                "react-native",
                "expo",
                "@react-native-community/cli",
            ],
        },
        "files": ["android/", "ios/", "AppDelegate.swift", "MainActivity.java", "pubspec.yaml"],
    },
    "web-app": {
        "package_json": {
            "dependencies": [
                "react",
                "vue",
                "@angular/core",
                "svelte",
                "next",
                "nuxt",
                "gatsby",
                "remix-run",
                "@astrojs",
            ],
            "devDependencies": [
                "vite",
                "webpack",
                "parcel",
                "eslint",
                "typescript",
            ],
        },
        "files": ["index.html", "public/", "src/App.", "src/main.", "vite.config.", "webpack.config."],
    },
    "ml-service": {
        "requirements": [
            "tensorflow",
            "torch",
            "pytorch",
            "keras",
            "scikit-learn",
            "transformers",
            "huggingface",
            "jax",
            "flax",
            "xgboost",
            "lightgbm",
            "onnx",
            "fastai",
        ],
        "pyproject": ["tensorflow", "torch", "pytorch", "scikit-learn", "transformers"],
        "files": ["model.py", "train.py", "inference.py", "models/", "checkpoints/", "saved_model/"],
    },
    "data-pipeline": {
        "requirements": [
            "pyspark",
            "apache-beam",
            "airflow",
            "prefect",
            "dagster",
            "dbt",
            "great-expectations",
            "snowflake",
            "redshift",
            "bigquery",
            "kafka",
            "pulumi",
        ],
        "pyproject": ["pyspark", "airflow", "prefect", "dagster", "dbt"],
        "files": ["dags/", "jobs/", "pipelines/", "etl/", "dbt_project.yml"],
    },
    "graphql-api": {
        "package_json": {
            "dependencies": [
                "graphql",
                "@apollo/server",
                "@apollo/client",
                "graphql-yoga",
                "apollo-server",
                "graphql-tools",
                "graphql-shield",
                "nexus",
                "giraphql",
                "ariadne",
            ],
        },
        "requirements": [
            "graphene",
            "strawberry-graphql",
            "ariadne",
            "graphql-core",
            "tartiflette",
        ],
        "files": ["schema.graphql", "resolvers/", "graphql/", ".gqlconfig"],
    },
    "microservice": {
        "files": [
            "docker-compose.yml",
            "kubernetes/",
            "k8s/",
            "helm/",
            "terraform/",
            "iaco/",
            ".kube/",
            "deployment.yaml",
            "service.yaml",
        ],
        "go_mod": [
            "micro",
            "grpc",
            "protobuf",
            "consul",
            "etcd",
            "jaeger",
            "opentracing",
        ],
        "requirements": [
            "grpcio",
            "protobuf",
            "consul",
            "etcd",
            "jaeger-client",
            "opentracing",
        ],
    },
}


class ProfileDetector:
    """Detects priority profile based on project files"""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize detector

        Args:
            project_root: Project root directory. Defaults to current working directory.
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self._scores: Dict[str, int] = {}

    def detect(self) -> str:
        """Detect the appropriate priority profile

        Returns:
            Detected profile name (defaults to "default" if no match)
        """
        self._scores = {}

        # Run all detection methods
        self._detect_from_package_json()
        self._detect_from_requirements()
        self._detect_from_pyproject()
        self._detect_from_go_mod()
        self._detect_from_files()
        self._detect_from_docker()

        # Find profile with highest score
        if self._scores:
            best_profile = max(self._scores.items(), key=lambda x: x[1])
            if best_profile[1] > 0:
                return best_profile[0]

        return "default"

    def get_detection_details(self) -> Dict[str, Any]:
        """Get details about the detection process

        Returns:
            Dict with detected profile, scores, and evidence
        """
        detected = self.detect()

        return {
            "detected_profile": detected,
            "scores": self._scores.copy(),
            "project_root": str(self.project_root),
        }

    def _detect_from_package_json(self) -> None:
        """Detect profile from package.json"""
        package_json = self.project_root / "package.json"
        if not package_json.exists():
            return

        try:
            import json
            with open(package_json, "r", encoding="utf-8") as f:
                content = json.load(f)

            deps = content.get("dependencies", {})
            dev_deps = content.get("devDependencies", {})
            all_deps = {**deps, **dev_deps}

            # Check each profile's patterns
            for profile_name, patterns in DETECTION_PATTERNS.items():
                profile_deps = patterns.get("package_json", {})
                score = 0

                for dep_list in profile_deps.values():
                    for dep in dep_list:
                        # Check for exact match or prefix match
                        if dep in all_deps or any(
                            d.startswith(dep + "@") for d in all_deps
                        ):
                            score += 1

                if score > 0:
                    self._scores[profile_name] = self._scores.get(profile_name, 0) + score

        except (json.JSONDecodeError, IOError):
            pass

    def _detect_from_requirements(self) -> None:
        """Detect profile from requirements.txt"""
        requirements_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements/base.txt",
            "requirements/prod.txt",
        ]

        all_requirements = set()
        for req_file in requirements_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                try:
                    with open(req_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip().lower()
                            # Extract package name (before version specifier)
                            if line and not line.startswith("#"):
                                pkg_name = re.split(r"[=<>~!]", line)[0].strip()
                                if pkg_name:
                                    all_requirements.add(pkg_name)
                except IOError:
                    pass

        # Check each profile's patterns
        for profile_name, patterns in DETECTION_PATTERNS.items():
            profile_reqs = patterns.get("requirements", [])
            score = sum(1 for req in profile_reqs if req in all_requirements)
            if score > 0:
                self._scores[profile_name] = self._scores.get(profile_name, 0) + score

    def _detect_from_pyproject(self) -> None:
        """Detect profile from pyproject.toml"""
        pyproject = self.project_root / "pyproject.toml"
        if not pyproject.exists():
            return

        try:
            import tomli
            with open(pyproject, "rb") as f:
                content = tomli.load(f)

            # Get dependencies from different sections
            all_deps = set()
            for section in ["dependencies", "dev-dependencies", "optional-dependencies"]:
                section_data = content.get("project", {}).get(section, {})
                if isinstance(section_data, list):
                    all_deps.update(
                        re.split(r"[=<>~!]", dep.lower())[0].strip()
                        for dep in section_data
                        if dep and not dep.startswith("#")
                    )
                elif isinstance(section_data, dict):
                    for group_deps in section_data.values():
                        if isinstance(group_deps, list):
                            all_deps.update(
                                re.split(r"[=<>~!]", dep.lower())[0].strip()
                                for dep in group_deps
                                if dep and not dep.startswith("#")
                            )

            # Check each profile's patterns
            for profile_name, patterns in DETECTION_PATTERNS.items():
                profile_deps = patterns.get("pyproject", [])
                score = sum(1 for dep in profile_deps if dep in all_deps)
                if score > 0:
                    self._scores[profile_name] = self._scores.get(profile_name, 0) + score

        except (ImportError, IOError):
            # tomli not available or parse error - skip
            pass

    def _detect_from_go_mod(self) -> None:
        """Detect profile from go.mod"""
        go_mod = self.project_root / "go.mod"
        if not go_mod.exists():
            return

        try:
            with open(go_mod, "r", encoding="utf-8") as f:
                content = f.read().lower()

            # Check each profile's patterns
            for profile_name, patterns in DETECTION_PATTERNS.items():
                profile_mods = patterns.get("go_mod", [])
                score = sum(1 for mod in profile_mods if mod in content)
                if score > 0:
                    self._scores[profile_name] = self._scores.get(profile_name, 0) + score

        except IOError:
            pass

    def _detect_from_files(self) -> None:
        """Detect profile from file/directory structure"""
        for profile_name, patterns in DETECTION_PATTERNS.items():
            file_patterns = patterns.get("files", [])
            score = 0

            for pattern in file_patterns:
                # Handle directory patterns (ending with /)
                if pattern.endswith("/"):
                    dir_path = self.project_root / pattern.rstrip("/")
                    if dir_path.is_dir():
                        score += 1
                # Handle wildcard patterns (containing . for extensions)
                elif "." in pattern and not pattern.startswith("."):
                    # Look for files matching the pattern
                    for file_path in self.project_root.rglob("*" + pattern.split("*")[0] if "*" in pattern else pattern):
                        if file_path.is_file() and pattern in file_path.name:
                            score += 1
                            break
                # Handle exact file matches
                else:
                    file_path = self.project_root / pattern
                    if file_path.exists():
                        score += 1

            if score > 0:
                self._scores[profile_name] = self._scores.get(profile_name, 0) + score

    def _detect_from_docker(self) -> None:
        """Detect profile from Docker configuration"""
        docker_files = ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"]

        has_docker = any(
            (self.project_root / f).exists() for f in docker_files
        )

        if has_docker:
            # Boost microservice score if Docker present
            self._scores["microservice"] = self._scores.get("microservice", 0) + 1


def detect_priority_profile(project_root: Optional[Path] = None) -> str:
    """Convenience function to detect priority profile

    Args:
        project_root: Project root directory. Defaults to current working directory.

    Returns:
        Detected profile name (defaults to "default" if no match)
    """
    detector = ProfileDetector(project_root)
    return detector.detect()


def get_detection_details(project_root: Optional[Path] = None) -> Dict[str, Any]:
    """Get detailed detection information

    Args:
        project_root: Project root directory. Defaults to current working directory.

    Returns:
        Dict with detection details
    """
    detector = ProfileDetector(project_root)
    return detector.get_detection_details()


def print_detection_details(details: Dict[str, Any]) -> str:
    """Format detection details for printing

    Args:
        details: Detection details from get_detection_details()

    Returns:
        Formatted string
    """
    lines = [
        f"Project Root: {details['project_root']}",
        f"Detected Profile: {details['detected_profile']}",
        "",
        "Detection Scores:",
    ]

    for profile, score in sorted(details["scores"].items(), key=lambda x: -x[1]):
        lines.append(f"  {profile}: {score}")

    return "\n".join(lines)


def print_detection_details_json(details: Optional[Dict[str, Any]] = None, project_root: Optional[Path] = None, indent: int = 2) -> str:
    """Format detection details as JSON

    Args:
        details: Detection details from get_detection_details() (optional)
        project_root: Project root directory (optional, used if details not provided)
        indent: JSON indentation (default: 2)

    Returns:
        JSON string with detection details
    """
    import json

    if details is None:
        details = get_detection_details(project_root)

    # Add evidence field for better context
    if "evidence" not in details:
        scores = details.get("scores", {})
        # Generate evidence from scores
        evidence = []
        for profile, score in sorted(scores.items(), key=lambda x: -x[1]):
            if score > 0:
                evidence.append(f"{profile} profile matched with score {score}")
        details["evidence"] = evidence

    return json.dumps(details, indent=indent)
