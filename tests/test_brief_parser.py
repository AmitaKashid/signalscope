from signalscope.application.brief_parser import BriefParser
from signalscope.domain.enums import DistributionChannel


def test_parser_extracts_channels_topics_audience_and_duration() -> None:
    parser = BriefParser()

    brief = parser.parse(
        raw_request=(
            "Find a short climate awareness video for 18-34 year olds for Instagram and the media library."
        ),
        explicit_channels=[],
    )

    assert DistributionChannel.SOCIAL in brief.requested_channels
    assert DistributionChannel.MEDIA_LIBRARY in brief.requested_channels
    assert "climate" in brief.topics
    assert brief.target_audience == "18-34"
    assert brief.maximum_duration_seconds == 60


def test_explicit_channels_override_inferred_channels() -> None:
    parser = BriefParser()

    brief = parser.parse(
        raw_request="Find an educational story for social media.",
        explicit_channels=[DistributionChannel.NEWSLETTER],
    )

    assert brief.requested_channels == [DistributionChannel.NEWSLETTER]
