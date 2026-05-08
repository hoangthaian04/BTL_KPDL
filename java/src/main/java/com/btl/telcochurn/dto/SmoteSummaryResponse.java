package com.btl.telcochurn.dto;

public record SmoteSummaryResponse(
        SmoteStageResponse before,
        SmoteStageResponse after
) {
}
