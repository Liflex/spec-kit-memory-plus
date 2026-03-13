"""
Priority Profiles Manager

Manages priority profiles for quality evaluation.
Provides utilities for listing, validating, and comparing profiles.
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import yaml
import json

from specify_cli.quality.models import CriteriaTemplate, PriorityProfile
from specify_cli.quality import autodetect


# Custom profiles file path
CUSTOM_PROFILES_PATH = Path(".speckit/priority-profiles.yml")


# Rule categories (Exp 46, Exp 48)
CATEGORY_TAGS = {
    "security": "Security, auth, encryption, input validation",
    "performance": "Performance optimization, caching, bundle size",
    "testing": "Test files, unit/integration/E2E tests",
    "documentation": "Documentation, README, guides",
    "code_quality": "Code quality, linting, formatting",
    # Exp 48: New category tags for platform templates
    "accessibility": "Accessibility, WCAG, keyboard navigation, ARIA",
    "ux_quality": "UI/UX quality, responsive design, user experience",
    "infrastructure": "Infrastructure as Code, Docker, Kubernetes, Terraform",
    "observability": "Monitoring, logging, tracing, metrics, alerts",
    "reliability": "High availability, disaster recovery, backup, scaling",
    "cicd": "CI/CD pipelines, deployment, automation",
    "correctness": "Functional correctness, happy path, edge cases",
}

# Domain tags definition
DOMAIN_TAGS = {
    "web": "Frontend web applications (React, Vue, Angular)",
    "api": "REST/GraphQL APIs and services",
    "data": "Database, data pipelines, and data processing",
    "infrastructure": "DevOps, IaC, cloud infrastructure",
    "mobile": "iOS/Android mobile applications",
    "ml": "Machine learning services and models",
    "graphql": "GraphQL-specific APIs and schemas",
    "microservices": "Distributed systems and microservices",
    "async": "Async/concurrent operations and messaging",
    "auth": "Authentication and authorization",
    "serverless": "Serverless functions and FaaS platforms (Lambda, Cloud Functions)",
    "realtime": "Real-time communication (WebSocket, SSE, live updates, event streaming)",
    "grpc": "gRPC services and streaming (Protobuf, server/client, observability)",
    "messaging": "Message queues and event streaming (RabbitMQ, Kafka, Redis Streams, SQS/SNS)",
    "caching": "Caching systems (Redis, Memcached, CDN, in-memory cache, cache invalidation)",
    "gateway": "API Gateway configuration (Kong, AWS API Gateway, NGINX, Traefik, Envoy)",
    "mesh": "Service Mesh configuration (Istio, Linkerd, Consul Connect, mTLS, traffic management, observability)",
    "container": "Container and Docker/K8s configuration (Dockerfile, Podman, containerd, Kubernetes, ECR/GCR/ACR)",
    "migration": "Database migrations (forward-only, rollback testing, transaction safety, idempotency)",
    "iac": "Infrastructure as Code (Terraform, CloudFormation, Pulumi, state management, drift detection)",
    "desktop": "Desktop applications (Electron, Tauri, cross-platform apps, native integration)",
}

# Built-in priority profiles (Exp 13)
BUILTIN_PRIORITY_PROFILES = {
    "default": {
        "multipliers": {
            "web": 1.0,
            "api": 1.0,
            "data": 1.0,
            "infrastructure": 1.0,
            "mobile": 1.0,
            "ml": 1.0,
            "graphql": 1.0,
            "microservices": 1.0,
            "async": 1.0,
            "auth": 1.0,
        },
        "description": "Default profile with neutral multipliers for all domains",
    },
    "web-app": {
        "multipliers": {
            "web": 1.5,
            "api": 1.2,
            "data": 1.0,
            "infrastructure": 1.0,
            "mobile": 0.5,
            "ml": 0.5,
            "graphql": 1.0,
            "microservices": 1.0,
            "async": 1.0,
            "auth": 1.2,
        },
        "description": "Web application profile with emphasis on frontend and API quality",
    },
    "mobile-app": {
        "multipliers": {
            "web": 0.5,
            "api": 1.3,
            "data": 1.2,
            "infrastructure": 0.8,
            "mobile": 2.0,
            "ml": 0.5,
            "graphql": 0.8,
            "microservices": 0.8,
            "async": 1.0,
            "auth": 1.5,
        },
        "description": "Mobile application profile with emphasis on mobile-specific quality",
    },
    "api-service": {
        "multipliers": {
            "web": 0.5,
            "api": 2.0,
            "data": 1.3,
            "infrastructure": 1.0,
            "mobile": 0.3,
            "ml": 0.8,
            "graphql": 1.3,
            "microservices": 1.2,
            "async": 1.2,
            "auth": 1.3,
        },
        "description": "API service profile with emphasis on API and data quality",
    },
    "ml-service": {
        "multipliers": {
            "web": 0.3,
            "api": 1.0,
            "data": 2.0,
            "infrastructure": 1.0,
            "mobile": 0.2,
            "ml": 2.0,
            "graphql": 0.5,
            "microservices": 0.8,
            "async": 1.0,
            "auth": 0.8,
        },
        "description": "ML service profile with emphasis on data and ML quality",
    },
    "data-pipeline": {
        "multipliers": {
            "web": 0.3,
            "api": 1.0,
            "data": 2.0,
            "infrastructure": 1.5,
            "mobile": 0.2,
            "ml": 1.5,
            "graphql": 0.3,
            "microservices": 1.3,
            "async": 1.5,
            "auth": 0.8,
        },
        "description": "Data pipeline profile with emphasis on data processing and infrastructure",
    },
}


class PriorityProfilesManager:
    """Manager for priority profiles"""

    @staticmethod
    def _load_custom_profiles(project_root: Optional[Path] = None) -> Dict[str, Any]:
        """Load custom priority profiles from .speckit/priority-profiles.yml

        Args:
            project_root: Project root directory. Defaults to current working directory.

        Returns:
            Dict of custom profiles (empty if file doesn't exist or is invalid)
        """
        if project_root is None:
            project_root = Path.cwd()

        custom_file = project_root / CUSTOM_PROFILES_PATH

        if not custom_file.exists():
            return {}

        try:
            with open(custom_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or not isinstance(data, dict):
                return {}

            # Extract profiles section
            profiles = data.get("priority_profiles", {})

            if not isinstance(profiles, dict):
                return {}

            return profiles

        except (yaml.YAMLError, IOError, OSError):
            # Invalid YAML or file read error - return empty dict
            return {}

    @staticmethod
    def _validate_profile_structure(profile: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate priority profile structure

        Args:
            profile: Profile dict to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required fields
        if "multipliers" not in profile:
            errors.append("Missing required field: multipliers")
        else:
            multipliers = profile["multipliers"]
            if not isinstance(multipliers, dict):
                errors.append("Field 'multipliers' must be a dict")
            else:
                # Validate multiplier values
                for domain, value in multipliers.items():
                    if not isinstance(value, (int, float)):
                        errors.append(f"Multiplier for '{domain}' must be a number")
                    elif value < 0:
                        errors.append(f"Multiplier for '{domain}' must be >= 0")

        # Description is optional but recommended
        # We'll just warn if missing, not fail

        return len(errors) == 0, errors

    @staticmethod
    def get_all_profiles(project_root: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
        """Get all profiles (built-in + custom), with custom overriding built-in

        Args:
            project_root: Project root directory for custom profiles

        Returns:
            Dict of all profiles with custom profiles taking precedence
        """
        # Start with built-in profiles
        all_profiles = BUILTIN_PRIORITY_PROFILES.copy()

        # Load and merge custom profiles
        custom_profiles = PriorityProfilesManager._load_custom_profiles(project_root)

        for name, profile in custom_profiles.items():
            is_valid, _ = PriorityProfilesManager._validate_profile_structure(profile)
            if is_valid:
                all_profiles[name] = profile

        return all_profiles

    @staticmethod
    def get_profile(name: str, project_root: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """Get a specific profile (custom or built-in)

        Args:
            name: Profile name
            project_root: Project root directory for custom profiles

        Returns:
            Profile dict or None if not found
        """
        # Check custom profiles first
        custom_profiles = PriorityProfilesManager._load_custom_profiles(project_root)

        if name in custom_profiles:
            profile = custom_profiles[name]
            is_valid, _ = PriorityProfilesManager._validate_profile_structure(profile)
            if is_valid:
                return profile

        # Fall back to built-in
        return BUILTIN_PRIORITY_PROFILES.get(name)

    @staticmethod
    def is_custom_profile(name: str, project_root: Optional[Path] = None) -> bool:
        """Check if a profile is custom (user-defined) or built-in

        Args:
            name: Profile name
            project_root: Project root directory for custom profiles

        Returns:
            True if profile is custom, False if built-in or not found
        """
        custom_profiles = PriorityProfilesManager._load_custom_profiles(project_root)
        return name in custom_profiles

    @staticmethod
    def list_all_profiles(project_root: Optional[Path] = None) -> List[str]:
        """List all available profile names (built-in + custom)

        Args:
            project_root: Project root directory for custom profiles

        Returns:
            List of profile names (custom first, then built-in)
        """
        all_profiles = PriorityProfilesManager.get_all_profiles(project_root)

        # Sort: custom profiles first, then built-in, alphabetically within each group
        custom = []
        builtin = []

        for name in all_profiles.keys():
            if PriorityProfilesManager.is_custom_profile(name, project_root):
                custom.append(name)
            else:
                builtin.append(name)

        custom.sort()
        builtin.sort()

        return custom + builtin

    @staticmethod
    def list_builtin_profiles() -> List[str]:
        """List built-in priority profile names

        Returns:
            List of profile names
        """
        return list(BUILTIN_PRIORITY_PROFILES.keys())

    @staticmethod
    def get_builtin_profile(name: str) -> Optional[Dict[str, Any]]:
        """Get built-in priority profile by name

        Args:
            name: Profile name

        Returns:
            Profile dict with multipliers and description, or None if not found
        """
        return BUILTIN_PRIORITY_PROFILES.get(name)

    @staticmethod
    def list_domain_tags() -> Dict[str, str]:
        """List all domain tags with descriptions

        Returns:
            Dict mapping domain tags to descriptions
        """
        return DOMAIN_TAGS.copy()

    @staticmethod
    def get_profile_summary(name: str, project_root: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """Get summary of a priority profile

        Args:
            name: Profile name
            project_root: Project root directory for custom profiles

        Returns:
            Summary dict with name, description, and top multipliers
        """
        profile = PriorityProfilesManager.get_profile(name, project_root)
        if not profile:
            return None

        multipliers = profile.get("multipliers", {})

        # Sort by multiplier (descending)
        sorted_multipliers = sorted(
            multipliers.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Get top 3
        top_multipliers = [
            {"domain": tag, "multiplier": mult}
            for tag, mult in sorted_multipliers[:3]
            if mult > 1.0
        ]

        return {
            "name": name,
            "description": profile.get("description", "No description"),
            "is_custom": PriorityProfilesManager.is_custom_profile(name, project_root),
            "top_domains": top_multipliers,
        }

    @staticmethod
    def get_all_profiles_summary(project_root: Optional[Path] = None) -> List[Dict[str, Any]]:
        """Get summary of all priority profiles

        Args:
            project_root: Project root directory for custom profiles

        Returns:
            List of profile summaries
        """
        return [
            PriorityProfilesManager.get_profile_summary(name, project_root)
            for name in PriorityProfilesManager.list_all_profiles(project_root)
        ]

    @staticmethod
    def compare_profiles(profile_names: List[str], project_root: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """Compare multiple priority profiles

        Args:
            profile_names: List of profile names to compare
            project_root: Project root directory for custom profiles

        Returns:
            Comparison dict with domain-by-domain multipliers
        """
        profiles = []
        for name in profile_names:
            profile = PriorityProfilesManager.get_profile(name, project_root)
            if not profile:
                return None
            profiles.append((name, profile))

        # Build comparison table
        comparison = {}
        for domain in DOMAIN_TAGS.keys():
            comparison[domain] = {}
            for name, profile in profiles:
                multipliers = profile.get("multipliers", {})
                comparison[domain][name] = multipliers.get(domain, 1.0)

        return {
            "profiles": profile_names,
            "domains": comparison,
        }

    @staticmethod
    def list_custom_profiles(project_root: Optional[Path] = None) -> List[str]:
        """List custom (user-defined) profile names

        Args:
            project_root: Project root directory for custom profiles

        Returns:
            List of custom profile names
        """
        custom_profiles = PriorityProfilesManager._load_custom_profiles(project_root)
        return list(custom_profiles.keys())

    @staticmethod
    def validate_custom_profiles(project_root: Optional[Path] = None) -> Dict[str, List[str]]:
        """Validate all custom profiles

        Args:
            project_root: Project root directory for custom profiles

        Returns:
            Dict mapping profile names to lists of validation errors
        """
        custom_profiles = PriorityProfilesManager._load_custom_profiles(project_root)
        errors = {}

        for name, profile in custom_profiles.items():
            is_valid, validation_errors = PriorityProfilesManager._validate_profile_structure(profile)
            if not is_valid:
                errors[name] = validation_errors

        return errors

    @staticmethod
    def get_custom_profiles_file_path(project_root: Optional[Path] = None) -> Path:
        """Get the path to the custom profiles file

        Args:
            project_root: Project root directory

        Returns:
            Path to .speckit/priority-profiles.yml
        """
        if project_root is None:
            project_root = Path.cwd()
        return project_root / CUSTOM_PROFILES_PATH

    @staticmethod
    def recommend_profile(description: str) -> Optional[str]:
        """Recommend a priority profile based on project description

        Args:
            description: Project description text

        Returns:
            Recommended profile name
        """
        if not description:
            return "default"

        desc_lower = description.lower()

        # Keyword mappings for profiles
        profile_keywords = {
            "mobile-app": ["mobile", "ios", "android", "app", "flutter", "react native", "swift", "kotlin"],
            "web-app": ["web", "frontend", "spa", "react", "vue", "angular", "javascript", "typescript"],
            "ml-service": ["ml", "machine learning", "ai", "model", "training", "inference", "tensorflow", "pytorch"],
            "data-pipeline": ["pipeline", "etl", "data warehouse", "spark", "kafka", "airflow", "batch processing"],
            "graphql-api": ["graphql", "gql", "apollo", "relay", "graph"],
            "microservice": ["microservice", "microservice", "distributed", "kafka", "event-driven"],
        }

        # Count matches for each profile
        profile_scores = {}
        for profile_name, keywords in profile_keywords.items():
            score = sum(1 for kw in keywords if kw in desc_lower)
            if score > 0:
                profile_scores[profile_name] = score

        # Return profile with highest score
        if profile_scores:
            return max(profile_scores.items(), key=lambda x: x[1])[0]

        return "default"

    @staticmethod
    def detect_profile(project_root: Optional[Path] = None) -> str:
        """Detect priority profile based on project files

        Args:
            project_root: Project root directory. Defaults to current working directory.

        Returns:
            Detected profile name (defaults to "default" if no match)
        """
        return autodetect.detect_priority_profile(project_root)

    @staticmethod
    def detect_profile_details(project_root: Optional[Path] = None) -> Dict[str, Any]:
        """Get detailed profile detection information

        Args:
            project_root: Project root directory. Defaults to current working directory.

        Returns:
            Dict with detected profile, scores, and evidence
        """
        return autodetect.get_detection_details(project_root)

    # ========== NEW: JSON Output Functions ==========

    @staticmethod
    def get_profile_json(name: str, project_root: Optional[Path] = None, indent: int = 2) -> Optional[str]:
        """Get JSON representation of a profile

        Args:
            name: Profile name
            project_root: Project root directory for custom profiles
            indent: JSON indentation (default: 2)

        Returns:
            JSON string or None if profile not found
        """
        profile = PriorityProfilesManager.get_profile(name, project_root)
        if not profile:
            return None

        data = {
            "name": name,
            "is_custom": PriorityProfilesManager.is_custom_profile(name, project_root),
            "description": profile.get("description", ""),
            "multipliers": profile.get("multipliers", {}),
        }

        return json.dumps(data, indent=indent)

    @staticmethod
    def get_all_profiles_json(project_root: Optional[Path] = None, indent: int = 2) -> str:
        """Get JSON representation of all profiles

        Args:
            project_root: Project root directory for custom profiles
            indent: JSON indentation (default: 2)

        Returns:
            JSON string with all profiles
        """
        all_profiles = PriorityProfilesManager.get_all_profiles(project_root)

        data = {
            "profiles": [],
            "total": len(all_profiles),
        }

        for name in sorted(all_profiles.keys()):
            profile = all_profiles[name]
            data["profiles"].append({
                "name": name,
                "is_custom": PriorityProfilesManager.is_custom_profile(name, project_root),
                "description": profile.get("description", ""),
                "multipliers": profile.get("multipliers", {}),
            })

        return json.dumps(data, indent=indent)

    @staticmethod
    def get_domain_tags_json(indent: int = 2) -> str:
        """Get JSON representation of all domain tags

        Args:
            indent: JSON indentation (default: 2)

        Returns:
            JSON string with domain tags
        """
        return json.dumps(DOMAIN_TAGS, indent=indent)

    @staticmethod
    def get_profile_comparison_json(profile_names: List[str], project_root: Optional[Path] = None, indent: int = 2) -> Optional[str]:
        """Get JSON representation of profile comparison

        Args:
            profile_names: List of profile names to compare
            project_root: Project root directory for custom profiles
            indent: JSON indentation (default: 2)

        Returns:
            JSON string with comparison or None if profiles not found
        """
        comparison = PriorityProfilesManager.compare_profiles(profile_names, project_root)
        if not comparison:
            return None

        # Add metadata
        result = {
            "comparison": comparison,
            "profile_count": len(profile_names),
            "domain_count": len(comparison.get("domains", {})),
        }

        return json.dumps(result, indent=indent)

    @staticmethod
    def get_profile_diff_json(profile1: str, profile2: str, project_root: Optional[Path] = None, indent: int = 2) -> Optional[str]:
        """Get JSON representation of profile diff

        Args:
            profile1: First profile name
            profile2: Second profile name
            project_root: Project root directory for custom profiles
            indent: JSON indentation (default: 2)

        Returns:
            JSON string with diff or None if profiles not found
        """
        diff = PriorityProfilesManager.diff_profiles(profile1, profile2, project_root)
        if not diff:
            return None

        # Add metadata for easier parsing
        result = {
            "diff": diff,
            "profile1": profile1,
            "profile2": profile2,
        }

        return json.dumps(result, indent=indent)

    @staticmethod
    def get_cascade_profile_info_json(cascade_str: str, project_root: Optional[Path] = None, strategy: str = "average", indent: int = 2) -> str:
        """Get JSON representation of cascade profile info

        Args:
            cascade_str: Cascade profile string
            project_root: Project root directory for custom profiles
            strategy: Merge strategy to use (default: "average")
            indent: JSON indentation (default: 2)

        Returns:
            JSON string with cascade profile info
        """
        info = PriorityProfilesManager.get_cascade_profile_info(cascade_str, project_root, strategy)

        # Ensure we always return a valid JSON
        if not info:
            info = {"error": "Unable to get cascade profile info", "cascade_str": cascade_str}

        return json.dumps(info, indent=indent)

    @staticmethod
    def get_profile_recommendation_json(description: str, indent: int = 2) -> str:
        """Get JSON representation of profile recommendation with scores

        Args:
            description: Project description text
            indent: JSON indentation (default: 2)

        Returns:
            JSON string with recommendation and scores
        """
        if not description:
            result = {
                "recommended_profile": "default",
                "description": description,
                "scores": {},
                "match_count": 0,
            }
            return json.dumps(result, indent=indent)

        desc_lower = description.lower()

        # Keyword mappings for profiles (same as recommend_profile)
        profile_keywords = {
            "mobile-app": ["mobile", "ios", "android", "app", "flutter", "react native", "swift", "kotlin"],
            "web-app": ["web", "frontend", "spa", "react", "vue", "angular", "javascript", "typescript"],
            "ml-service": ["ml", "machine learning", "ai", "model", "training", "inference", "tensorflow", "pytorch"],
            "data-pipeline": ["pipeline", "etl", "data warehouse", "spark", "kafka", "airflow", "batch processing"],
            "graphql-api": ["graphql", "gql", "apollo", "relay", "graph"],
            "microservice": ["microservice", "microservice", "distributed", "kafka", "event-driven"],
        }

        # Count matches for each profile
        profile_scores = {}
        matched_keywords = {}
        for profile_name, keywords in profile_keywords.items():
            matched = [kw for kw in keywords if kw in desc_lower]
            if matched:
                profile_scores[profile_name] = len(matched)
                matched_keywords[profile_name] = matched

        # Get recommended profile
        recommended = "default"
        if profile_scores:
            recommended = max(profile_scores.items(), key=lambda x: x[1])[0]

        result = {
            "recommended_profile": recommended,
            "description": description,
            "scores": profile_scores,
            "matched_keywords": matched_keywords,
            "match_count": sum(profile_scores.values()),
        }

        return json.dumps(result, indent=indent)

    @staticmethod
    def get_cascade_recommendation_json(description: str, project_root: Optional[Path] = None, indent: int = 2) -> str:
        """Get JSON representation of cascade recommendation with scores

        Args:
            description: Project description text
            project_root: Project root directory for custom profiles
            indent: JSON indentation (default: 2)

        Returns:
            JSON string with cascade recommendation and scores
        """
        if not description:
            result = {
                "recommended_cascade": None,
                "description": description,
                "scores": {},
                "matched_keywords": {},
                "is_hybrid": False,
            }
            return json.dumps(result, indent=indent)

        desc_lower = description.lower()

        # Hybrid project patterns (same as recommend_cascade)
        hybrid_patterns = {
            "fullstack": ["fullstack", "full stack", "web and mobile", "react native", "flutter", "ios and android"],
            "web-ml": ["web ml", "ml web app", "ai web", "machine learning frontend", "tensorflow web"],
            "mobile-ml": ["mobile ml", "ml mobile", "ai mobile", "on-device ml", "coreml", "tflite mobile"],
            "api-ml": ["ml api", "ml service", "model api", "inference api", "ml backend"],
            "graphql-web": ["graphql web", "gql frontend", "apollo react", "graphql spa"],
            "microservice-ml": ["ml microservice", "distributed ml", "kafka ml", "ml service mesh"],
        }

        # Score each pattern
        pattern_scores = {}
        matched_keywords = {}
        for pattern_name, keywords in hybrid_patterns.items():
            matched = [kw for kw in keywords if kw in desc_lower]
            if matched:
                pattern_scores[pattern_name] = len(matched)
                matched_keywords[pattern_name] = matched

        # Map patterns to cascade profiles
        cascade_map = {
            "fullstack": "web-app+mobile-app",
            "web-ml": "web-app+ml-service",
            "mobile-ml": "mobile-app+ml-service",
            "api-ml": "api+ml-service",
            "graphql-web": "graphql-api+web-app",
            "microservice-ml": "microservice+ml-service",
        }

        recommended_cascade = None
        best_pattern = None
        if pattern_scores:
            best_pattern = max(pattern_scores.items(), key=lambda x: x[1])[0]
            recommended_cascade = cascade_map.get(best_pattern)

        result = {
            "recommended_cascade": recommended_cascade,
            "recommended_pattern": best_pattern,
            "description": description,
            "scores": pattern_scores,
            "matched_keywords": matched_keywords,
            "is_hybrid": bool(pattern_scores),
            "cascade_map": cascade_map,
        }

        return json.dumps(result, indent=indent)

    @staticmethod
    def get_custom_profiles_json(project_root: Optional[Path] = None, indent: int = 2) -> str:
        """Get JSON representation of custom profiles

        Args:
            project_root: Project root directory for custom profiles
            indent: JSON indentation (default: 2)

        Returns:
            JSON string with custom profiles info
        """
        custom_profiles = PriorityProfilesManager.list_custom_profiles(project_root)
        file_path = PriorityProfilesManager.get_custom_profiles_file_path(project_root)

        profiles_data = []
        for name in custom_profiles:
            profile = PriorityProfilesManager.get_profile(name, project_root)
            if profile:
                profiles_data.append({
                    "name": name,
                    "description": profile.get("description", ""),
                    "multipliers": profile.get("multipliers", {}),
                })

        result = {
            "custom_profiles": profiles_data,
            "count": len(custom_profiles),
            "file_path": str(file_path),
            "file_exists": file_path.exists(),
        }

        return json.dumps(result, indent=indent)

    # ========== NEW: Profile Diff Function ==========

    @staticmethod
    def diff_profiles(profile1: str, profile2: str, project_root: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """Compare two profiles and highlight differences

        Args:
            profile1: First profile name
            profile2: Second profile name
            project_root: Project root directory for custom profiles

        Returns:
            Dict with differences highlighted
        """
        p1 = PriorityProfilesManager.get_profile(profile1, project_root)
        p2 = PriorityProfilesManager.get_profile(profile2, project_root)

        if not p1 or not p2:
            return None

        m1 = p1.get("multipliers", {})
        m2 = p2.get("multipliers", {})

        # Find differences
        differences = {}
        similar = {}

        for domain in DOMAIN_TAGS.keys():
            v1 = m1.get(domain, 1.0)
            v2 = m2.get(domain, 1.0)
            diff = v2 - v1

            if abs(diff) > 0.01:  # Significant difference
                differences[domain] = {
                    profile1: v1,
                    profile2: v2,
                    "difference": round(diff, 2),
                    "change": "increased" if diff > 0 else "decreased",
                }
            else:
                similar[domain] = v1

        return {
            "profile1": profile1,
            "profile2": profile2,
            "differences": differences,
            "similar": similar,
            "difference_count": len(differences),
        }

    @staticmethod
    def print_profile_diff(profile1: str, profile2: str, project_root: Optional[Path] = None) -> str:
        """Get formatted profile diff for printing

        Args:
            profile1: First profile name
            profile2: Second profile name
            project_root: Project root directory for custom profiles

        Returns:
            Formatted string
        """
        diff = PriorityProfilesManager.diff_profiles(profile1, profile2, project_root)

        if not diff:
            return f"Profile diff failed: one or both profiles not found"

        lines = [
            f"=== Profile Diff: {profile1} vs {profile2} ===",
            "",
        ]

        if diff["differences"]:
            lines.append(f"Differences ({diff['difference_count']} domains):")
            lines.append("")

            for domain, data in sorted(diff["differences"].items(), key=lambda x: abs(x[1]["difference"]), reverse=True):
                v1 = data[profile1]
                v2 = data[profile2]
                change = data["change"]
                diff_val = data["difference"]

                arrow = "↑" if change == "increased" else "↓"
                lines.append(f"  {domain}: {v1}x → {v2}x ({arrow} {abs(diff_val)})")

            lines.append("")

        if diff["similar"]:
            similar_domains = ", ".join(sorted(diff["similar"].keys()))
            lines.append(f"Similar domains: {similar_domains}")

        return "\n".join(lines)

    # ========== NEW: Profile Merge Function ==========

    @staticmethod
    def merge_profiles(
        profile_names: List[str],
        merged_name: str,
        project_root: Optional[Path] = None,
        strategy: str = "average",
        weights: Optional[List[float]] = None
    ) -> Optional[Dict[str, Any]]:
        """Merge multiple profiles into a new profile

        Args:
            profile_names: List of profile names to merge
            merged_name: Name for the merged profile
            project_root: Project root directory for custom profiles
            strategy: Merge strategy - "average" (default), "max", "min", or "weighted"
            weights: Optional weights for each profile (only used with "weighted" strategy)

        Returns:
            Merged profile dict or None if any profile not found
        """
        profiles = []
        for name in profile_names:
            profile = PriorityProfilesManager.get_profile(name, project_root)
            if not profile:
                return None
            profiles.append(profile)

        # Validate weights for weighted strategy
        if strategy == "weighted":
            if weights is None:
                # Equal weights if not specified
                weights = [1.0] * len(profile_names)
            elif len(weights) != len(profile_names):
                return None  # Mismatched weights length

            # Normalize weights to sum to 1.0
            total_weight = sum(weights)
            if total_weight == 0:
                return None  # Invalid weights

            weights = [w / total_weight for w in weights]

        # Merge multipliers based on strategy
        merged_multipliers = {}

        for domain in DOMAIN_TAGS.keys():
            values = [p.get("multipliers", {}).get(domain, 1.0) for p in profiles]

            if strategy == "max":
                merged_multipliers[domain] = max(values)
            elif strategy == "min":
                merged_multipliers[domain] = min(values)
            elif strategy == "weighted":
                # Weighted average
                weighted_sum = sum(v * w for v, w in zip(values, weights))
                merged_multipliers[domain] = round(weighted_sum, 2)
            else:  # average
                merged_multipliers[domain] = round(sum(values) / len(values), 2)

        # Generate description
        profile_list = ", ".join(profile_names)

        if strategy == "weighted":
            weight_str = ", ".join(f"{w:.2f}" for w in weights)
            description = f"Merged profile (weighted strategy, weights: [{weight_str}]) from: {profile_list}"
        elif strategy == "max":
            description = f"Merged profile (max strategy) from: {profile_list}"
        elif strategy == "min":
            description = f"Merged profile (min strategy) from: {profile_list}"
        else:
            description = f"Merged profile (average strategy) from: {profile_list}"

        result = {
            "name": merged_name,
            "description": description,
            "multipliers": merged_multipliers,
            "source_profiles": profile_names,
            "merge_strategy": strategy,
        }

        # Add weights if using weighted strategy
        if strategy == "weighted":
            result["weights"] = weights

        return result

    # ========== NEW: Enhanced Validation ==========

    @staticmethod
    def validate_and_print(project_root: Optional[Path] = None) -> str:
        """Validate custom profiles and return formatted results

        Args:
            project_root: Project root directory for custom profiles

        Returns:
            Formatted validation results
        """
        custom_profiles = PriorityProfilesManager._load_custom_profiles(project_root)
        custom_file = PriorityProfilesManager.get_custom_profiles_file_path(project_root)

        lines = ["### Profile Validation", ""]

        if not custom_profiles:
            lines.append(f"No custom profiles found at: {custom_file}")
            return "\n".join(lines)

        errors = PriorityProfilesManager.validate_custom_profiles(project_root)
        valid_count = len(custom_profiles) - len(errors)

        lines.append(f"Custom profiles file: {custom_file}")
        lines.append(f"Total profiles: {len(custom_profiles)}")
        lines.append(f"Valid: {valid_count}")
        lines.append(f"Invalid: {len(errors)}")
        lines.append("")

        if errors:
            lines.append("❌ Validation Errors:")
            lines.append("")
            for profile_name, profile_errors in sorted(errors.items()):
                lines.append(f"  {profile_name}:")
                for error in profile_errors:
                    lines.append(f"    - {error}")
        else:
            lines.append("✅ All custom profiles are valid!")

        return "\n".join(lines)

    @staticmethod
    def get_validation_report_json(project_root: Optional[Path] = None, indent: int = 2) -> str:
        """Get JSON validation report for custom profiles

        Args:
            project_root: Project root directory for custom profiles
            indent: JSON indentation (default: 2)

        Returns:
            JSON string with validation report
        """
        custom_profiles = PriorityProfilesManager._load_custom_profiles(project_root)
        errors = PriorityProfilesManager.validate_custom_profiles(project_root)

        data = {
            "custom_profiles_file": str(PriorityProfilesManager.get_custom_profiles_file_path(project_root)),
            "total_profiles": len(custom_profiles),
            "valid_profiles": len(custom_profiles) - len(errors),
            "invalid_profiles": len(errors),
            "profiles": [],
        }

        for name in sorted(custom_profiles.keys()):
            is_custom = PriorityProfilesManager.is_custom_profile(name, project_root)
            profile_errors = errors.get(name, [])

            data["profiles"].append({
                "name": name,
                "valid": len(profile_errors) == 0,
                "errors": profile_errors,
            })

        return json.dumps(data, indent=indent)

    # ========== NEW: Cascade Multipliers (Exp 20) ==========

    @staticmethod
    def parse_cascade_profile(cascade_str: str) -> Tuple[bool, List[str], Optional[str]]:
        """Parse cascade profile string (e.g., "web-app+mobile-app")

        Args:
            cascade_str: Profile string that may contain "+" for cascade

        Returns:
            Tuple of (is_cascade, profile_names, error_message)
            - is_cascade: True if this is a cascade profile
            - profile_names: List of profile names to cascade
            - error_message: Error message if parsing failed, None otherwise
        """
        if not cascade_str:
            return False, [], None

        # Check for cascade syntax (contains "+")
        if "+" not in cascade_str:
            return False, [cascade_str], None

        # Split by "+" and validate
        profile_names = [p.strip() for p in cascade_str.split("+") if p.strip()]

        if not profile_names:
            return False, [], f"Invalid cascade profile: '{cascade_str}' - no profiles found"

        if len(profile_names) < 2:
            return False, [], f"Invalid cascade profile: '{cascade_str}' - need at least 2 profiles"

        # Check for duplicate profiles
        if len(profile_names) != len(set(profile_names)):
            return False, [], f"Invalid cascade profile: '{cascade_str}' - duplicate profiles detected"

        return True, profile_names, None

    @staticmethod
    def parse_weighted_cascade_profile(cascade_str: str) -> Tuple[bool, List[str], List[float], Optional[str]]:
        """Parse weighted cascade profile string (e.g., "web-app:2+mobile-app:1")

        Args:
            cascade_str: Profile string with optional weights (profile:weight format)

        Returns:
            Tuple of (is_cascade, profile_names, weights, error_message)
            - is_cascade: True if this is a cascade profile
            - profile_names: List of profile names
            - weights: List of weights (1.0 if not specified)
            - error_message: Error message if parsing failed
        """
        if not cascade_str:
            return False, [], [], None

        # Check for cascade syntax (contains "+")
        if "+" not in cascade_str:
            return False, [cascade_str], [1.0], None

        # Split by "+" and parse each part
        parts = [p.strip() for p in cascade_str.split("+") if p.strip()]

        if not parts:
            return False, [], [], f"Invalid cascade profile: '{cascade_str}' - no profiles found"

        if len(parts) < 2:
            return False, [], [], f"Invalid cascade profile: '{cascade_str}' - need at least 2 profiles"

        profile_names = []
        weights = []

        for part in parts:
            # Check for weight syntax (profile:weight)
            if ":" in part:
                name, weight_str = part.rsplit(":", 1)
                name = name.strip()
                try:
                    weight = float(weight_str.strip())
                    if weight <= 0:
                        return False, [], [], f"Invalid weight in '{part}' - must be positive"
                except ValueError:
                    return False, [], [], f"Invalid weight in '{part}' - must be a number"
            else:
                name = part.strip()
                weight = 1.0

            profile_names.append(name)
            weights.append(weight)

        # Check for duplicate profiles
        if len(profile_names) != len(set(profile_names)):
            return False, [], [], f"Invalid cascade profile: '{cascade_str}' - duplicate profiles detected"

        return True, profile_names, weights, None

    @staticmethod
    def resolve_cascade_profile(
        cascade_str: str,
        project_root: Optional[Path] = None,
        strategy: str = "average",
        weights: Optional[List[float]] = None
    ) -> Optional[Dict[str, Any]]:
        """Resolve cascade profile string into a merged profile

        Args:
            cascade_str: Cascade profile string (e.g., "web-app+mobile-app" or "web-app:2+mobile-app:1")
            project_root: Project root directory for custom profiles
            strategy: Merge strategy - "average" (default), "max", "min", or "weighted"
            weights: Optional explicit weights (overrides cascade string weights if provided)

        Returns:
            Merged profile dict or None if any profile not found
        """
        # Try weighted parse first
        is_weighted, profile_names, cascade_weights, error = PriorityProfilesManager.parse_weighted_cascade_profile(cascade_str)

        if error:
            return None

        if not is_weighted:
            # Single profile - just return it
            return PriorityProfilesManager.get_profile(cascade_str, project_root)

        # Use provided weights or cascade weights
        merge_weights = weights if weights is not None else cascade_weights

        # If weights were detected in cascade string, default to weighted strategy
        if strategy == "average" and merge_weights != [1.0] * len(profile_names):
            strategy = "weighted"

        # Merge profiles
        merged_name = f"cascade:{'+'.join(profile_names)}"

        # Only pass weights if using weighted strategy
        if strategy == "weighted":
            return PriorityProfilesManager.merge_profiles(profile_names, merged_name, project_root, strategy, merge_weights)
        else:
            return PriorityProfilesManager.merge_profiles(profile_names, merged_name, project_root, strategy)

    @staticmethod
    def get_cascade_profile_info(
        cascade_str: str,
        project_root: Optional[Path] = None,
        strategy: str = "average"
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a cascade profile

        Args:
            cascade_str: Cascade profile string
            project_root: Project root directory for custom profiles
            strategy: Merge strategy to use (default: "average")

        Returns:
            Dict with cascade profile info or None if invalid
        """
        is_weighted, profile_names, weights, error = PriorityProfilesManager.parse_weighted_cascade_profile(cascade_str)

        if error:
            return {"error": error, "cascade_str": cascade_str}

        if not is_weighted:
            return {
                "cascade_str": cascade_str,
                "is_cascade": False,
                "profile": cascade_str,
            }

        # Verify all profiles exist
        profiles = []
        missing = []

        for name in profile_names:
            profile = PriorityProfilesManager.get_profile(name, project_root)
            if profile:
                profiles.append((name, profile))
            else:
                missing.append(name)

        if missing:
            return {
                "error": f"Profiles not found: {', '.join(missing)}",
                "cascade_str": cascade_str,
                "missing_profiles": missing,
            }

        # Get cascade profile
        merged = PriorityProfilesManager.resolve_cascade_profile(cascade_str, project_root, strategy)

        if not merged:
            return {"error": "Failed to resolve cascade profile", "cascade_str": cascade_str}

        result = {
            "cascade_str": cascade_str,
            "is_cascade": True,
            "source_profiles": profile_names,
            "merged_multipliers": merged.get("multipliers", {}),
            "description": merged.get("description", ""),
            "profile_count": len(profile_names),
            "strategy": merged.get("merge_strategy", strategy),
        }

        # Add weights if using weighted strategy or if weights were specified
        if merged.get("weights") or weights != [1.0] * len(profile_names):
            result["weights"] = merged.get("weights", weights)

        return result

    @staticmethod
    def print_cascade_profile_info(
        cascade_str: str,
        project_root: Optional[Path] = None,
        strategy: str = "average"
    ) -> str:
        """Get formatted cascade profile information for printing

        Args:
            cascade_str: Cascade profile string
            project_root: Project root directory for custom profiles
            strategy: Merge strategy to use (default: "average")

        Returns:
            Formatted string
        """
        info = PriorityProfilesManager.get_cascade_profile_info(cascade_str, project_root, strategy)

        lines = [f"### Cascade Profile: {cascade_str}", ""]

        if "error" in info:
            lines.append(f"❌ Error: {info['error']}")
            return "\n".join(lines)

        if not info.get("is_cascade"):
            lines.append(f"Note: '{cascade_str}' is a single profile, not a cascade.")
            profile_summary = PriorityProfilesManager.get_profile_summary(cascade_str, project_root)
            if profile_summary:
                lines.append("")
                lines.append(print_profile_summary(cascade_str, project_root))
            return "\n".join(lines)

        # Display cascade information
        source_profiles = info.get("source_profiles", [])
        lines.append(f"Source profiles ({len(source_profiles)}):")
        for name in source_profiles:
            lines.append(f"  - {name}")

        # Display weights if present
        if "weights" in info:
            weights = info["weights"]
            weight_str = ", ".join(f"{name}={w:.2f}" for name, w in zip(source_profiles, weights))
            lines.append(f"  Weights: {weight_str}")

        # Display strategy
        strategy_display = info.get("strategy", strategy)
        lines.append(f"  Strategy: {strategy_display}")
        lines.append("")

        # Display merged multipliers
        multipliers = info.get("merged_multipliers", {})
        sorted_multipliers = sorted(multipliers.items(), key=lambda x: x[1], reverse=True)

        lines.append(f"Merged multipliers ({strategy_display} strategy):")
        for domain, value in sorted_multipliers:
            if value > 1.0:
                lines.append(f"  • {domain}: {value}x")
        lines.append("")

        # Show source comparison
        lines.append("Source profile breakdown:")
        for domain in DOMAIN_TAGS.keys():
            values = []
            for name in source_profiles:
                profile = PriorityProfilesManager.get_profile(name, project_root)
                if profile:
                    mult = profile.get("multipliers", {}).get(domain, 1.0)
                    values.append(f"{name}={mult}x")

            merged_val = multipliers.get(domain, 1.0)
            if merged_val > 1.0 or any("x" in v and "=1." not in v for v in values):
                lines.append(f"  {domain}: {', '.join(values)} → {merged_val}x")

        return "\n".join(lines)

    @staticmethod
    def list_available_cascades(project_root: Optional[Path] = None) -> List[str]:
        """List common useful cascade combinations

        Args:
            project_root: Project root directory for custom profiles

        Returns:
            List of suggested cascade combinations
        """
        all_profiles = PriorityProfilesManager.list_all_profiles(project_root)

        # Define common hybrid combinations
        common_cascades = [
            ("web-app", "mobile-app"),  # Fullstack apps
            ("web-app", "ml-service"),  # Web + ML
            ("api", "data-pipeline"),  # API + Data
            ("mobile-app", "ml-service"),  # Mobile + ML
            ("graphql-api", "web-app"),  # GraphQL + Web
            ("microservice", "ml-service"),  # Microservice + ML
            ("web-app", "api"),  # Web + API (fullstack)
        ]

        # Filter to only include profiles that exist
        valid_cascades = []
        for p1, p2 in common_cascades:
            if p1 in all_profiles and p2 in all_profiles:
                valid_cascades.append(f"{p1}+{p2}")

        return valid_cascades

    @staticmethod
    def recommend_cascade(description: str, project_root: Optional[Path] = None) -> Optional[str]:
        """Recommend a cascade profile based on project description

        Args:
            description: Project description text
            project_root: Project root directory for custom profiles

        Returns:
            Recommended cascade profile string or None
        """
        if not description:
            return None

        desc_lower = description.lower()

        # Hybrid project patterns
        hybrid_patterns = {
            "fullstack": ["fullstack", "full stack", "web and mobile", "react native", "flutter", "ios and android"],
            "web-ml": ["web ml", "ml web app", "ai web", "machine learning frontend", "tensorflow web"],
            "mobile-ml": ["mobile ml", "ml mobile", "ai mobile", "on-device ml", "coreml", "tflite mobile"],
            "api-ml": ["ml api", "ml service", "model api", "inference api", "ml backend"],
            "graphql-web": ["graphql web", "gql frontend", "apollo react", "graphql spa"],
            "microservice-ml": ["ml microservice", "distributed ml", "kafka ml", "ml service mesh"],
        }

        # Score each pattern
        pattern_scores = {}
        for pattern_name, keywords in hybrid_patterns.items():
            score = sum(1 for kw in keywords if kw in desc_lower)
            if score > 0:
                pattern_scores[pattern_name] = score

        if not pattern_scores:
            return None

        # Map patterns to cascade profiles
        cascade_map = {
            "fullstack": "web-app+mobile-app",
            "web-ml": "web-app+ml-service",
            "mobile-ml": "mobile-app+ml-service",
            "api-ml": "api+ml-service",
            "graphql-web": "graphql-api+web-app",
            "microservice-ml": "microservice+ml-service",
        }

        best_pattern = max(pattern_scores.items(), key=lambda x: x[1])[0]
        return cascade_map.get(best_pattern)

    @staticmethod
    def get_cascade_presets() -> Dict[str, Dict[str, Any]]:
        """Get predefined cascade profile presets

        Returns:
            Dict mapping preset names to cascade configuration
        """
        return {
            "fullstack-balanced": {
                "cascade": "web-app:1+mobile-app:1",
                "description": "Equal emphasis on web and mobile",
                "strategy": "average",
                "use_case": "Applications with both web and mobile clients",
            },
            "fullstack-web-first": {
                "cascade": "web-app:2+mobile-app:1",
                "description": "Web-focused fullstack (2x weight on web)",
                "strategy": "weighted",
                "use_case": "Primary web UI with mobile companion app",
            },
            "web-ml": {
                "cascade": "web-app+ml-service",
                "description": "Web application with ML backend",
                "strategy": "average",
                "use_case": "Web apps using AI/ML features",
            },
            "mobile-ml": {
                "cascade": "mobile-app:2+ml-service:1",
                "description": "Mobile-first ML application",
                "strategy": "weighted",
                "use_case": "Mobile apps with on-device or cloud ML",
            },
            "api-data": {
                "cascade": "api+data-pipeline",
                "description": "API with data processing pipeline",
                "strategy": "average",
                "use_case": "Data-driven APIs and analytics",
            },
            "graphql-web": {
                "cascade": "graphql-api+web-app",
                "description": "GraphQL API with web frontend",
                "strategy": "average",
                "use_case": "Modern web apps using GraphQL",
            },
            "microservice-ml": {
                "cascade": "microservice+ml-service",
                "description": "Distributed ML service",
                "strategy": "average",
                "use_case": "Scalable ML infrastructure",
            },
            "conservative": {
                "cascade": "web-app+mobile-app",
                "description": "Conservative merging (min strategy)",
                "strategy": "min",
                "use_case": "Minimal quality requirements, faster iteration",
            },
            "aggressive": {
                "cascade": "web-app+mobile-app",
                "description": "Aggressive merging (max strategy)",
                "strategy": "max",
                "use_case": "Maximum quality enforcement across all domains",
            },
        }

    @staticmethod
    def list_merge_strategies() -> List[str]:
        """List available merge strategies

        Returns:
            List of strategy names with descriptions
        """
        return [
            "average - Average multipliers (balanced approach, default)",
            "max - Take maximum multiplier (strict quality enforcement)",
            "min - Take minimum multiplier (lenient quality requirements)",
            "weighted - Weighted average (custom weights per profile)",
        ]

    @staticmethod
    def compare_strategies(
        cascade_str: str,
        project_root: Optional[Path] = None,
        include_weighted: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Compare cascade merge strategies (average, max, min, weighted)

        Args:
            cascade_str: Cascade profile string (e.g., "web-app+mobile-app")
            project_root: Project root directory for custom profiles
            include_weighted: Include weighted strategy (default: False)

        Returns:
            Dict with strategy comparison results or None if invalid cascade
        """
        # Parse cascade profile
        is_weighted, profile_names, weights, error = PriorityProfilesManager.parse_weighted_cascade_profile(cascade_str)

        if error:
            return {"error": error, "cascade_str": cascade_str}

        if not is_weighted:
            return {"error": "Not a cascade profile", "cascade_str": cascade_str, "is_cascade": False}

        # Verify all profiles exist
        profiles = []
        missing = []

        for name in profile_names:
            profile = PriorityProfilesManager.get_profile(name, project_root)
            if profile:
                profiles.append((name, profile))
            else:
                missing.append(name)

        if missing:
            return {"error": f"Profiles not found: {', '.join(missing)}", "missing_profiles": missing}

        # Get merged profile for each strategy
        strategies_to_compare = ["average", "max", "min"]
        if include_weighted and weights != [1.0] * len(profile_names):
            strategies_to_compare.append("weighted")

        results = {}
        all_domains = set()

        for strategy in strategies_to_compare:
            # Resolve cascade profile for this strategy
            if strategy == "weighted" and include_weighted:
                merged = PriorityProfilesManager.resolve_cascade_profile(
                    cascade_str, project_root, strategy, weights
                )
            else:
                merged = PriorityProfilesManager.resolve_cascade_profile(
                    cascade_str, project_root, strategy
                )

            if merged:
                multipliers = merged.get("multipliers", {})
                results[strategy] = {
                    "multipliers": multipliers,
                    "description": merged.get("description", ""),
                }
                all_domains.update(multipliers.keys())

        # Calculate statistics for each strategy
        stats = {}
        for strategy, data in results.items():
            mults = list(data["multipliers"].values())
            if mults:
                stats[strategy] = {
                    "max": round(max(mults), 2),
                    "min": round(min(mults), 2),
                    "avg": round(sum(mults) / len(mults), 2),
                }

        # Generate recommendation based on characteristics
        recommendation = PriorityProfilesManager._recommend_strategy(results, stats)

        return {
            "cascade_str": cascade_str,
            "source_profiles": profile_names,
            "strategies": results,
            "statistics": stats,
            "recommendation": recommendation,
            "all_domains": sorted(all_domains),
        }

    @staticmethod
    def _recommend_strategy(
        strategies: Dict[str, Any],
        stats: Dict[str, Dict[str, float]]
    ) -> str:
        """Generate strategy recommendation based on cascade characteristics

        Args:
            strategies: Strategy results with multipliers
            stats: Statistics for each strategy (max, min, avg)

        Returns:
            Recommended strategy name with explanation
        """
        # Analyze variance in average strategy
        avg_mults = strategies.get("average", {}).get("multipliers", {})
        if avg_mults:
            values = list(avg_mults.values())
            variance = max(values) - min(values)

            if variance < 0.3:
                return "average (low variance, balanced approach)"
            elif variance > 0.8:
                return "max (high variance, strict quality recommended)"
            else:
                # Check for specific patterns
                max_stats = stats.get("max", {})
                min_stats = stats.get("min", {})

                if max_stats.get("avg", 0) > 1.3 and min_stats.get("avg", 0) < 0.9:
                    return "max (significant boosts in key domains)"
                elif min_stats.get("avg", 0) > 1.1:
                    return "min (all domains moderately boosted, lenient sufficient)"

        return "average (balanced approach)"

    @staticmethod
    def analyze_profile_rules(
        profile_name: str,
        criteria_name: str,
        project_root: Optional[Path] = None,
        phase: str = "B"
    ) -> Optional[Dict[str, Any]]:
        """Analyze rules by priority for a specific profile and criteria

        Args:
            profile_name: Priority profile name
            criteria_name: Criteria template name (e.g., "frontend", "backend")
            project_root: Project root directory for custom profiles
            phase: Phase to analyze ("A" or "B", default: "B")

        Returns:
            Analysis dict with top_rules, critical_rules, domain_distribution, gaps
        """
        # Get profile
        profile = PriorityProfilesManager.get_profile(profile_name, project_root)
        if not profile:
            return None

        multipliers = profile.get("multipliers", {})

        # Load criteria template
        from specify_cli.quality.rules import RulesRepository

        rules_repo = RulesRepository()
        try:
            criteria = rules_repo.load_criteria(criteria_name)
        except Exception:
            return None

        # Get active rules for phase
        from specify_cli.quality.models import Phase

        phase_key = phase.lower()
        active_rules = [
            rule for rule in criteria.rules
            if rule.phase.value.lower() == phase_key
        ]

        if not active_rules:
            # Try uppercase phase value
            active_rules = [
                rule for rule in criteria.rules
                if rule.phase.value == phase
            ]

        # Calculate effective weights for all rules
        rule_scores = []
        critical_rules = []
        domain_counts: Dict[str, int] = {}

        for rule in active_rules:
            # Get effective weight with multipliers
            effective_weight = rule.get_effective_weight(multipliers)

            rule_info = {
                "id": rule.id,
                "description": rule.description,
                "severity": rule.severity.value,
                "base_weight": rule.weight,
                "domain_tags": rule.domain_tags.copy() if rule.domain_tags else [],
                "effective_weight": round(effective_weight, 2),
                "phase": rule.phase.value,
            }

            rule_scores.append(rule_info)

            # Track critical rules (fail severity)
            if rule.severity.value == "fail":
                critical_rules.append(rule_info)

            # Count domains
            if rule.domain_tags:
                for tag in rule.domain_tags:
                    domain_counts[tag] = domain_counts.get(tag, 0) + 1

        # Sort by effective weight (descending)
        rule_scores.sort(key=lambda x: x["effective_weight"], reverse=True)

        # Get top 10 rules by effective weight
        top_rules = rule_scores[:10]

        # Domain distribution
        domain_distribution = []
        for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
            multiplier = multipliers.get(domain, 1.0)
            domain_distribution.append({
                "domain": domain,
                "rule_count": count,
                "multiplier": multiplier,
                "emphasis": "high" if multiplier > 1.3 else "medium" if multiplier > 1.0 else "low"
            })

        # Find gaps (domains with low multiplier but high rule count)
        gaps = []
        for domain, count in domain_counts.items():
            multiplier = multipliers.get(domain, 1.0)
            if count >= 2 and multiplier < 1.0:
                gaps.append({
                    "domain": domain,
                    "rule_count": count,
                    "multiplier": multiplier,
                    "impact": round(count * (1.0 - multiplier), 1)
                })

        gaps.sort(key=lambda x: x["impact"], reverse=True)

        return {
            "profile": {
                "name": profile_name,
                "description": profile.get("description", ""),
                "is_custom": PriorityProfilesManager.is_custom_profile(profile_name, project_root),
            },
            "criteria": {
                "name": criteria_name,
                "description": criteria.description,
                "version": criteria.version,
                "total_rules": len(criteria.rules),
                "phase_rules": len(active_rules),
                "phase": phase,
            },
            "top_rules": top_rules,
            "critical_rules": critical_rules,
            "domain_distribution": domain_distribution,
            "gaps": gaps,
            "multipliers": multipliers,
        }


def print_profile_summary(profile_name: str, project_root: Optional[Path] = None) -> str:
    """Get formatted summary of a profile for printing

    Args:
        profile_name: Profile name
        project_root: Project root directory for custom profiles

    Returns:
        Formatted string
    """
    summary = PriorityProfilesManager.get_profile_summary(profile_name, project_root)
    if not summary:
        return f"Profile '{profile_name}' not found"

    lines = [
        f"Profile: {summary['name']}",
    ]

    if summary.get("is_custom"):
        lines.append("Type: Custom (user-defined)")
    else:
        lines.append("Type: Built-in")

    lines.append(f"Description: {summary['description']}")

    if summary["top_domains"]:
        lines.append("\nTop emphasized domains:")
        for item in summary["top_domains"]:
            domain = item["domain"]
            mult = item["multiplier"]
            desc = DOMAIN_TAGS.get(domain, "")
            lines.append(f"  - {domain}: {mult}x ({desc})")

    return "\n".join(lines)


def print_all_profiles(project_root: Optional[Path] = None) -> str:
    """Get formatted list of all profiles for printing

    Args:
        project_root: Project root directory for custom profiles

    Returns:
        Formatted string
    """
    summaries = PriorityProfilesManager.get_all_profiles_summary(project_root)

    lines = ["Available Priority Profiles:", ""]

    # Group by type
    custom = [s for s in summaries if s.get("is_custom")]
    builtin = [s for s in summaries if not s.get("is_custom")]

    if custom:
        lines.append("### Custom Profiles")
        for summary in custom:
            lines.append(f"• {summary['name']}")
            lines.append(f"  {summary['description']}")

            if summary["top_domains"]:
                top_str = ", ".join(
                    f"{d['domain']} ({d['multiplier']}x)"
                    for d in summary["top_domains"]
                )
                lines.append(f"  Emphasizes: {top_str}")

            lines.append("")

    if builtin:
        lines.append("### Built-in Profiles")
        for summary in builtin:
            lines.append(f"• {summary['name']}")
            lines.append(f"  {summary['description']}")

            if summary["top_domains"]:
                top_str = ", ".join(
                    f"{d['domain']} ({d['multiplier']}x)"
                    for d in summary["top_domains"]
                )
                lines.append(f"  Emphasizes: {top_str}")

            lines.append("")

    return "\n".join(lines).rstrip()


def print_custom_profiles_info(project_root: Optional[Path] = None) -> str:
    """Get info about custom profiles

    Args:
        project_root: Project root directory for custom profiles

    Returns:
        Formatted string
    """
    custom_profiles = PriorityProfilesManager._load_custom_profiles(project_root)
    custom_file = PriorityProfilesManager.get_custom_profiles_file_path(project_root)

    lines = ["### Custom Priority Profiles", ""]

    if not custom_profiles:
        lines.append(f"No custom profiles defined.")
        lines.append(f"")
        lines.append(f"To create custom profiles, add a file at:")
        lines.append(f"  {custom_file}")
        lines.append(f"")
        lines.append(f"Example format:")
        lines.append(f"```yaml")
        lines.append(f"priority_profiles:")
        lines.append(f"  my-custom-profile:")
        lines.append(f"    multipliers:")
        lines.append(f"      web: 2.0")
        lines.append(f"      api: 1.5")
        lines.append(f"      auth: 1.8")
        lines.append(f"    description: \"My custom profile for web apps\"")
        lines.append(f"```")
    else:
        lines.append(f"Custom profiles file: {custom_file}")
        lines.append(f"")
        lines.append(f"Custom profiles ({len(custom_profiles)}):")
        for name in sorted(custom_profiles.keys()):
            lines.append(f"  - {name}")

        # Validation
        errors = PriorityProfilesManager.validate_custom_profiles(project_root)
        if errors:
            lines.append(f"")
            lines.append(f"⚠️ Validation errors:")
            for profile_name, profile_errors in errors.items():
                lines.append(f"  {profile_name}:")
                for error in profile_errors:
                    lines.append(f"    - {error}")
        else:
            lines.append(f"")
            lines.append(f"✅ All custom profiles are valid")

    return "\n".join(lines)


def print_profile_analysis(
    profile_name: str,
    criteria_name: str,
    project_root: Optional[Path] = None,
    phase: str = "B",
    max_rules: int = 10
) -> str:
    """Print quality gap analysis for a profile and criteria

    Args:
        profile_name: Priority profile name
        criteria_name: Criteria template name
        project_root: Project root directory for custom profiles
        phase: Phase to analyze ("A" or "B", default: "B")
        max_rules: Maximum number of top rules to show

    Returns:
        Formatted string with analysis
    """
    analysis = PriorityProfilesManager.analyze_profile_rules(
        profile_name, criteria_name, project_root, phase
    )

    if not analysis:
        return f"❌ Profile '{profile_name}' or criteria '{criteria_name}' not found"

    lines = []
    lines.append("### Quality Gap Analysis")
    lines.append("")

    # Header
    profile = analysis["profile"]
    criteria = analysis["criteria"]

    lines.append(f"**Profile:** {profile['name']}")
    if profile["description"]:
        lines.append(f"**Description:** {profile['description']}")
    if profile["is_custom"]:
        lines.append(f"**Type:** Custom profile")
    lines.append("")

    lines.append(f"**Criteria:** {criteria['name']} v{criteria['version']}")
    lines.append(f"**Description:** {criteria['description']}")
    lines.append(f"**Phase:** {criteria['phase']} ({criteria['phase_rules']} active rules)")
    lines.append("")

    lines.append("---")
    lines.append("")

    # Top Rules by Effective Weight
    lines.append(f"#### Top {max_rules} Rules by Priority Score")
    lines.append("")
    lines.append("Rules with highest effective weight (base × multiplier):")
    lines.append("")

    if analysis["top_rules"]:
        lines.append("| Rank | Rule ID | Description | Severity | Base | Effective | Domains |")
        lines.append("|------|---------|-------------|----------|------|-----------|---------|")

        for i, rule in enumerate(analysis["top_rules"][:max_rules], 1):
            domains = ", ".join(rule["domain_tags"]) if rule["domain_tags"] else "none"
            severity_emoji = "🔴" if rule["severity"] == "fail" else "🟡"
            lines.append(
                f"| {i} | {rule['id']} | {rule['description'][:50]}... "
                f"| {severity_emoji} {rule['severity']} | {rule['base_weight']} | "
                f"**{rule['effective_weight']}** | {domains} |"
            )
    else:
        lines.append("No rules found for this phase")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Critical Rules (fail severity)
    lines.append(f"#### Critical Rules ({len(analysis['critical_rules'])} rules)")
    lines.append("")

    if analysis["critical_rules"]:
        lines.append("Rules with `fail` severity that must pass:")
        lines.append("")

        for rule in analysis["critical_rules"]:
            domains = ", ".join(rule["domain_tags"]) if rule["domain_tags"] else "none"
            lines.append(f"- **{rule['id']}**: {rule['description']}")
            lines.append(f"  - Severity: fail | Weight: {rule['base_weight']} | Effective: **{rule['effective_weight']}**")
            lines.append(f"  - Domains: {domains}")
            lines.append("")
    else:
        lines.append("No critical rules for this phase")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Domain Distribution
    lines.append("#### Domain Distribution")
    lines.append("")

    if analysis["domain_distribution"]:
        lines.append("| Domain | Rule Count | Multiplier | Emphasis |")
        lines.append("|--------|------------|------------|----------|")

        for dist in analysis["domain_distribution"]:
            emphasis_emoji = {
                "high": "🔥",
                "medium": "⚡",
                "low": "💤"
            }.get(dist["emphasis"], "")

            lines.append(
                f"| {dist['domain']} | {dist['rule_count']} | "
                f"{dist['multiplier']}x | {emphasis_emoji} {dist['emphasis']} |"
            )
    else:
        lines.append("No domain tags found in rules")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Gap Detection
    lines.append("#### Gap Detection")
    lines.append("")

    if analysis["gaps"]:
        lines.append("Domains with many rules but low multiplier (potential gaps):")
        lines.append("")
        lines.append("| Domain | Rule Count | Multiplier | Impact |")
        lines.append("|--------|------------|------------|--------|")

        for gap in analysis["gaps"]:
            lines.append(
                f"| {gap['domain']} | {gap['rule_count']} | "
                f"{gap['multiplier']}x | -{gap['impact']} |"
            )
        lines.append("")
        lines.append("*Consider increasing multiplier for these domains if they're important for your project*")
    else:
        lines.append("✅ No significant gaps detected")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Multipliers Reference
    lines.append("#### Multipliers Reference")
    lines.append("")
    lines.append("| Domain | Multiplier |")
    lines.append("|--------|------------|")

    for domain in sorted(analysis["multipliers"].keys()):
        mult = analysis["multipliers"][domain]
        lines.append(f"| {domain} | {mult}x |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Usage Examples
    lines.append("#### Usage Examples")
    lines.append("")
    lines.append("Run quality loop with this profile:")
    lines.append("")
    lines.append("```bash")
    lines.append(f"/speckit.loop --criteria {criteria_name} --priority-profile {profile_name}")
    lines.append("```")
    lines.append("")

    # Compare with other profiles
    lines.append("Compare profiles:")
    lines.append("")
    lines.append("```bash")
    lines.append(f"/speckit.profiles compare {profile_name} default")
    lines.append(f"/speckit.profiles compare {profile_name} web-app")
    lines.append("```")
    lines.append("")

    # Cascade suggestion
    lines.append("For hybrid projects, consider cascade profiles:")
    lines.append("")
    lines.append("```bash")
    lines.append(f"/speckit.loop --criteria {criteria_name} --priority-profile {profile_name}+ml-service")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def print_strategy_comparison(
    cascade_str: str,
    project_root: Optional[Path] = None,
    include_weighted: bool = False
) -> str:
    """Print cascade merge strategies comparison in formatted text

    Args:
        cascade_str: Cascade profile string (e.g., "web-app+mobile-app")
        project_root: Project root directory for custom profiles
        include_weighted: Include weighted strategy (default: False)

    Returns:
        Formatted text with strategy comparison
    """
    result = PriorityProfilesManager.compare_strategies(cascade_str, project_root, include_weighted)

    if not result:
        return f"### Strategy Comparison Error\n\nInvalid cascade profile: {cascade_str}"

    if "error" in result:
        return f"### Strategy Comparison Error\n\n{result['error']}\n\nCascade: {cascade_str}"

    lines = []
    lines.append(f"### Strategy Comparison: {cascade_str}")
    lines.append("")
    lines.append(f"Source profiles: {', '.join(result['source_profiles'])}")
    lines.append("")

    # Multiplier comparison table
    lines.append("## Multiplier Comparison by Strategy")
    lines.append("")

    # Get all domains sorted
    domains = result.get('all_domains', [])

    if domains:
        # Header
        strategies = list(result['strategies'].keys())
        header = f"{'Domain':<15} " + "".join(f"{s:<12} " for s in strategies)
        lines.append(header)
        lines.append("-" * len(header))

        # Rows
        for domain in domains:
            row_values = []
            for strategy in strategies:
                mult = result['strategies'][strategy]['multipliers'].get(domain, 1.0)
                # Format with highlights
                if mult > 1.3:
                    row_values.append(f"**{mult}**    ")
                elif mult < 0.8:
                    row_values.append(f"*{mult}*     ")
                else:
                    row_values.append(f"{mult}       ")
            row = f"{domain:<15} " + "".join(f"{v:<12}" for v in row_values)
            lines.append(row)

    lines.append("")

    # Statistics
    lines.append("## Strategy Statistics")
    lines.append("")

    for strategy, stat in result['statistics'].items():
        lines.append(f"{strategy:<12} : max={stat['max']}x, min={stat['min']}x, avg={stat['avg']}x")

    lines.append("")
    lines.append(f"**Recommendation:** {result['recommendation']}")
    lines.append("")

    # Strategy descriptions
    lines.append("## Strategy Descriptions")
    lines.append("")

    strategy_descriptions = {
        "average": """
**average** (avg, mean, bal)
  - Average multipliers (balanced approach)
  - Use case: Equal emphasis on all source profiles
""",
        "max": """
**max** (strict)
  - Take maximum multiplier
  - Use case: Strict quality enforcement across all domains
""",
        "min": """
**min** (lenient)
  - Take minimum multiplier
  - Use case: Minimal quality requirements, faster iteration
""",
        "weighted": """
**weighted** (wgt, custom)
  - Weighted average based on profile weights
  - Use case: Custom emphasis per source profile
""",
    }

    for strategy in result['strategies'].keys():
        lines.append(strategy_descriptions.get(strategy, ""))

    # Understanding output
    lines.append("**Understanding the output:**")
    lines.append("- **Bold values** (e.g., `**2.00**`) indicate significantly boosted multipliers (> 1.3x)")
    lines.append("- **Italic values** (e.g., `*0.80*`) indicate reduced multipliers (< 0.8x)")
    lines.append("- **average strategy**: Balanced approach, takes average of source multipliers")
    lines.append("- **max strategy**: Strict approach, takes highest multiplier from source profiles")
    lines.append("- **min strategy**: Lenient approach, takes lowest multiplier from source profiles")
    lines.append("- **weighted strategy**: Custom approach with user-defined weights per profile")
    lines.append("")

    return "\n".join(lines)



def print_strategy_comparison_json(
    cascade_str: str,
    project_root: Optional[Path] = None,
    include_weighted: bool = False,
    indent: int = 2
) -> str:
    """Print cascade merge strategies comparison in JSON format

    Args:
        cascade_str: Cascade profile string (e.g., "web-app+mobile-app")
        project_root: Project root directory for custom profiles
        include_weighted: Include weighted strategy (default: False)
        indent: JSON indentation (default: 2)

    Returns:
        JSON string with strategy comparison
    """
    result = PriorityProfilesManager.compare_strategies(cascade_str, project_root, include_weighted)

    if not result:
        return json.dumps({
            "error": "Invalid cascade profile",
            "cascade_str": cascade_str
        }, indent=indent)

    if "error" in result:
        return json.dumps(result, indent=indent)

    # Build clean JSON output
    output = {
        "cascade_str": result["cascade_str"],
        "source_profiles": result["source_profiles"],
        "strategies": {},
        "statistics": result["statistics"],
        "recommendation": result["recommendation"],
    }

    # Format strategies for cleaner output
    for strategy, data in result["strategies"].items():
        output["strategies"][strategy] = {
            "multipliers": data["multipliers"],
            "description": data["description"],
        }

    return json.dumps(output, indent=indent)


def print_all_profiles_json(project_root: Optional[Path] = None, indent: int = 2) -> str:
    """Print all profiles in JSON format (for list mode)

    Args:
        project_root: Project root directory for custom profiles
        indent: JSON indentation (default: 2)

    Returns:
        JSON string with all profiles
    """
    return PriorityProfilesManager.get_all_profiles_json(project_root, indent)


def print_profile_summary_json(profile_name: str, project_root: Optional[Path] = None, indent: int = 2) -> str:
    """Print profile summary in JSON format (for show mode)

    Args:
        profile_name: Profile name
        project_root: Project root directory for custom profiles
        indent: JSON indentation (default: 2)

    Returns:
        JSON string with profile details
    """
    result = PriorityProfilesManager.get_profile_json(profile_name, project_root, indent)
    if result is None:
        return json.dumps({
            "error": "Profile not found",
            "profile_name": profile_name
        }, indent=indent)
    return result


def print_domain_tags_json(indent: int = 2) -> str:
    """Print domain tags in JSON format (for domains mode)

    Args:
        indent: JSON indentation (default: 2)

    Returns:
        JSON string with domain tags
    """
    return PriorityProfilesManager.get_domain_tags_json(indent)


def print_profile_comparison_json(profile_names: List[str], project_root: Optional[Path] = None, indent: int = 2) -> Optional[str]:
    """Print profile comparison in JSON format (for compare mode)

    Args:
        profile_names: List of profile names to compare
        project_root: Project root directory for custom profiles
        indent: JSON indentation (default: 2)

    Returns:
        JSON string with comparison or None if profiles not found
    """
    return PriorityProfilesManager.get_profile_comparison_json(profile_names, project_root, indent)


def print_profile_diff_json(profile1: str, profile2: str, project_root: Optional[Path] = None, indent: int = 2) -> Optional[str]:
    """Print profile diff in JSON format (for diff mode)

    Args:
        profile1: First profile name
        profile2: Second profile name
        project_root: Project root directory for custom profiles
        indent: JSON indentation (default: 2)

    Returns:
        JSON string with diff or None if profiles not found
    """
    return PriorityProfilesManager.get_profile_diff_json(profile1, profile2, project_root, indent)


def print_cascade_profile_info_json(cascade_str: str, project_root: Optional[Path] = None, strategy: str = "average", indent: int = 2) -> str:
    """Print cascade profile info in JSON format (for cascade mode)

    Args:
        cascade_str: Cascade profile string
        project_root: Project root directory for custom profiles
        strategy: Merge strategy to use (default: "average")
        indent: JSON indentation (default: 2)

    Returns:
        JSON string with cascade profile info
    """
    return PriorityProfilesManager.get_cascade_profile_info_json(cascade_str, project_root, strategy, indent)


def print_profile_recommendation_json(description: str, indent: int = 2) -> str:
    """Print profile recommendation in JSON format (for recommend mode)

    Args:
        description: Project description text
        indent: JSON indentation (default: 2)

    Returns:
        JSON string with recommendation and scores
    """
    return PriorityProfilesManager.get_profile_recommendation_json(description, indent)


def print_cascade_recommendation_json(description: str, project_root: Optional[Path] = None, indent: int = 2) -> str:
    """Print cascade recommendation in JSON format (for recommend-cascade mode)

    Args:
        description: Project description text
        project_root: Project root directory for custom profiles
        indent: JSON indentation (default: 2)

    Returns:
        JSON string with cascade recommendation and scores
    """
    return PriorityProfilesManager.get_cascade_recommendation_json(description, project_root, indent)


def print_custom_profiles_json(project_root: Optional[Path] = None, indent: int = 2) -> str:
    """Print custom profiles in JSON format (for custom mode)

    Args:
        project_root: Project root directory for custom profiles
        indent: JSON indentation (default: 2)

    Returns:
        JSON string with custom profiles info
    """
    return PriorityProfilesManager.get_custom_profiles_json(project_root, indent)


def interactive_profile_wizard(
    project_root: Optional[Path] = None,
    project_description: Optional[str] = None,
    criteria_name: Optional[str] = None,
) -> str:
    """Run an interactive profile selection wizard

    The wizard guides users through profile selection by:
    1. Auto-detecting project context (if available)
    2. Asking clarifying questions about project type
    3. Showing top recommendations with confidence scores
    4. Providing profile comparison
    5. Guiding cascade/strategy selection for hybrid projects
    6. Outputting ready-to-use command

    Args:
        project_root: Project root directory for auto-detection
        project_description: Optional pre-provided project description
        criteria_name: Optional criteria name for command output

    Returns:
        Formatted wizard output with recommendations and ready-to-use command
    """
    lines = [
        "### 🧙 Interactive Profile Selection Wizard",
        "",
    ]

    # Step 1: Auto-detect project context
    lines.append("#### Step 1: Auto-Detection")
    lines.append("")

    detected_profile = None
    detection_details = None

    if project_root:
        try:
            detected_profile = autodetect.detect_priority_profile(project_root)
            detection_details = autodetect.get_detection_details(project_root)
        except Exception:
            pass  # Auto-detection is optional

    if detected_profile and detected_profile != "default":
        lines.append(f"✅ **Auto-detected profile:** `{detected_profile}`")

        if detection_details and detection_details.get("evidence"):
            lines.append("")
            lines.append("**Detection evidence:**")
            for evidence in detection_details["evidence"][:3]:  # Show top 3
                lines.append(f"  - {evidence}")
    else:
        lines.append("⚠️ **No profile auto-detected**")
        lines.append("  Could not detect project type from files.")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Step 2: Get recommendations
    lines.append("#### Step 2: Profile Recommendations")
    lines.append("")

    if project_description:
        # Use intelligent recommender with description
        from specify_cli.quality.priority_profiles import (
            recommend_profiles_intelligent,
        )

        lines.append(f"**Based on:** {project_description}")
        lines.append("")

        result = recommend_profiles_intelligent(project_description, top_n=3)

        if result.get("recommendations"):
            for i, rec in enumerate(result["recommendations"], 1):
                profile = rec["profile"]
                score = rec["score"]
                confidence = rec.get("confidence", "none").upper()
                reason = rec.get("reason", "")

                confidence_icon = {
                    "HIGH": "🟢",
                    "MEDIUM": "🟡",
                    "LOW": "🟠",
                    "NONE": "⚪",
                }.get(confidence, "⚪")

                lines.append(f"{i}. **{profile}** {confidence_icon} (score: {score})")
                lines.append(f"   Confidence: {confidence}")
                lines.append(f"   Reason: {reason}")

                if rec.get("factors"):
                    factors = rec["factors"]
                    lines.append(f"   Factors: tech={factors.get('tech_stack', 0)}, "
                               f"type={factors.get('project_type', 0)}, "
                               f"priorities={factors.get('priorities', 0)}")
                lines.append("")

        # Hybrid suggestion
        if result.get("cascade_suggestion"):
            lines.append(f"💡 **Hybrid Suggestion:** `{result['cascade_suggestion']}`")
            lines.append("")
    else:
        # Use detected profile or list top profiles
        profiles_to_show = []

        if detected_profile and detected_profile != "default":
            profiles_to_show.append(detected_profile)

        # Add common profiles
        for profile in ["web-app", "mobile-app", "ml-service", "graphql-api", "data-pipeline"]:
            if profile not in profiles_to_show:
                profiles_to_show.append(profile)
            if len(profiles_to_show) >= 5:
                break

        lines.append("**Common profiles:**")
        lines.append("")

        for i, profile_name in enumerate(profiles_to_show, 1):
            profile = PriorityProfilesManager.get_profile(profile_name, project_root)
            if profile:
                description = profile.get("description", "")
                multipliers = profile.get("multipliers", {})

                # Get top domains
                top_domains = sorted(
                    multipliers.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]

                top_str = ", ".join(f"{d} ({m}x)" for d, m in top_domains if m > 1.0)

                lines.append(f"{i}. **{profile_name}**")
                lines.append(f"   {description}")
                if top_str:
                    lines.append(f"   Emphasizes: {top_str}")
                lines.append("")

    lines.append("---")
    lines.append("")

    # Step 3: Profile comparison
    lines.append("#### Step 3: Profile Comparison")
    lines.append("")

    # Compare top 3 profiles
    profiles_to_compare = ["web-app", "mobile-app", "ml-service"]
    comparison = PriorityProfilesManager.compare_profiles(profiles_to_compare)

    if comparison:
        # Header row
        header = f"{'Domain':<15} " + " ".join(f"{p:<12}" for p in profiles_to_compare)
        lines.append(header)
        lines.append("-" * len(header))

        # Domain rows (showing key domains)
        key_domains = ["web", "mobile", "api", "data", "ml", "auth"]

        for domain in key_domains:
            values = []
            for profile in profiles_to_compare:
                prof = PriorityProfilesManager.get_profile(profile, project_root)
                mult = prof.get("multipliers", {}).get(domain, 1.0) if prof else 1.0
                values.append(f"{mult}x")
            row = f"{domain:<15} " + " ".join(f"{v:<12}" for v in values)
            lines.append(row)

    lines.append("")
    lines.append("*Run `/speckit.profiles compare <profile1> <profile2> [...]` for detailed comparison*")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Step 4: Cascade options for hybrid projects
    lines.append("#### Step 4: Hybrid Projects (Cascade Profiles)")
    lines.append("")

    lines.append("If your project spans multiple domains, you can combine profiles:")
    lines.append("")

    cascade_examples = [
        ("fullstack-balanced", "Equal web + mobile emphasis"),
        ("web-ml", "Web application with ML backend"),
        ("mobile-ml", "Mobile-first ML application"),
        ("graphql-web", "GraphQL API with web frontend"),
        ("api-data", "API with data processing"),
    ]

    for preset, description in cascade_examples:
        lines.append(f"- **{preset}** - {description}")

    lines.append("")
    lines.append("**Or create custom cascades:**")
    lines.append("- `web-app+mobile-app` - Combine profiles (average strategy)")
    lines.append("- `web-app:2+mobile-app:1` - Weighted (2x emphasis on web)")
    lines.append("- `--strategy max` - Use strict quality for cascades")
    lines.append("")
    lines.append("*Run `/speckit.profiles presets` to see all named presets*")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Step 5: Ready-to-use commands
    lines.append("#### Step 5: Ready-to-Use Commands")
    lines.append("")

    # Build command based on recommendations
    criteria = criteria_name or "backend"

    if detected_profile and detected_profile != "default":
        lines.append("**Using auto-detected profile:**")
        lines.append("")
        lines.append("```bash")
        lines.append(f"/speckit.loop --criteria {criteria} --priority-profile {detected_profile}")
        lines.append("```")
        lines.append("")

    lines.append("**Using specific profiles:**")
    lines.append("")
    lines.append("```bash")
    lines.append(f"/speckit.loop --criteria {criteria} --priority-profile web-app")
    lines.append(f"/speckit.loop --criteria {criteria} --priority-profile mobile-app")
    lines.append(f"/speckit.loop --criteria {criteria} --priority-profile ml-service")
    lines.append("```")
    lines.append("")

    lines.append("**Using cascade profiles (hybrid projects):**")
    lines.append("")
    lines.append("```bash")
    lines.append(f"/speckit.loop --criteria {criteria} --priority-profile fullstack-balanced")
    lines.append(f"/speckit.loop --criteria {criteria} --priority-profile web-app+mobile-app")
    lines.append(f"/speckit.loop --criteria {criteria} --priority-profile web-ml")
    lines.append("```")
    lines.append("")

    lines.append("**With merge strategy:**")
    lines.append("")
    lines.append("```bash")
    lines.append(f"/speckit.loop --criteria {criteria} --priority-profile web-app+mobile-app --strategy max")
    lines.append(f"/speckit.loop --criteria {criteria} --priority-profile web-app+mobile-app --strategy min")
    lines.append(f"/speckit.loop --criteria {criteria} --priority-profile web-app+mobile-app --strategy avg")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Additional help
    lines.append("#### Additional Help")
    lines.append("")
    lines.append("- `/speckit.profiles list` - List all available profiles")
    lines.append("- `/speckit.profiles show <name>` - Show detailed profile info")
    lines.append("- `/speckit.profiles compare <profile1> <profile2>` - Compare profiles")
    lines.append("- `/speckit.profiles detect` - Auto-detect profile from project")
    lines.append("- `/speckit.profiles recommend \"<description>\"` - Get recommendations")
    lines.append("- `/speckit.profiles cascade <profile1+profile2>` - Preview cascade")
    lines.append("- `/speckit.profiles compare-strategies <cascade>` - Compare strategies")
    lines.append("- `/speckit.profiles presets` - List named cascade presets")

    return "\n".join(lines)
