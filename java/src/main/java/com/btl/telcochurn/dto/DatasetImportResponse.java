package com.btl.telcochurn.dto;

public record DatasetImportResponse(
        String status,
        String sourceFile,
        String datasetPath,
        int rowsBefore,
        int incomingRows,
        int importedRows,
        int skippedRows,
        int duplicateRowsRemoved,
        int rowsAfter
) {
}
