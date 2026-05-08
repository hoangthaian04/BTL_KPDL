package com.btl.telcochurn.dto;

public record SmoteStageResponse(
        int churnNo,
        int churnYes,
        int total
) {
}
