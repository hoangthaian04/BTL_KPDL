package com.btl.telcochurn.dto;

public record DashboardSummaryResponse(
        int datasetRows,
        int featureColumns,
        int trainRowsBeforeSmote,
        int balancedTrainRows,
        String bestModel,
        double accuracy,
        double precision,
        double recall,
        double f1,
        double rocAuc,
        SmoteSummaryResponse smoteSummary,
        String dashboardPath
) {
}
