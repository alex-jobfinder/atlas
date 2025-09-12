"""
Creative service for testing different creative formats and configurations.
"""

from typing import Dict, Any, Optional, List


def test_creative(format: str, duration: Optional[int] = None, interactive: bool = False) -> Dict[str, Any]:
    """
    Test different creative formats and configurations.

    Args:
        format: Creative format to test (video, banner, native, etc.)
        duration: Duration in seconds (for video)
        interactive: Test interactive elements

    Returns:
        Dictionary containing testing results and recommendations
    """
    # Base recommendations for all formats
    base_recommendations = [
        "Test multiple durations (15s, 30s, 60s)",
        "A/B test interactive vs static elements",
        "Monitor engagement metrics closely"
    ]

    # Format-specific recommendations
    format_recommendations = {
        "video": [
            "Test different video lengths",
            "Optimize for mobile viewing",
            "Include captions for accessibility"
        ],
        "banner": [
            "Test different banner sizes",
            "Optimize for viewability",
            "Use clear call-to-action buttons"
        ],
        "native": [
            "Match platform design guidelines",
            "Test different headline variations",
            "Optimize for organic feel"
        ]
    }

    # Interactive-specific recommendations
    if interactive:
        base_recommendations.extend([
            "Test user interaction patterns",
            "Monitor engagement time",
            "Optimize for mobile touch interfaces"
        ])

    # Combine recommendations
    all_recommendations = base_recommendations + format_recommendations.get(format, [])

    result = {
        "format": format,
        "duration": duration,
        "interactive": interactive,
        "recommendations": all_recommendations,
        "test_type": "creative_format",
        "estimated_test_duration": "2-4 weeks"
    }

    # Add format-specific insights
    if format == "video" and duration:
        if duration <= 15:
            result["video_optimization"] = "Short-form optimized for social"
        elif duration <= 30:
            result["video_optimization"] = "Standard length for most platforms"
        else:
            result["video_optimization"] = "Long-form for detailed messaging"

    return result
