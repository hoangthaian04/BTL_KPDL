package com.btl.telcochurn.dto;

import java.util.Map;

public record PredictionRequest(
        Map<String, Object> customer
) {
}
