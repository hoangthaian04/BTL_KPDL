package com.btl.telcochurn.controller;

import com.btl.telcochurn.dto.DatasetImportResponse;
import com.btl.telcochurn.service.DatasetImportService;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/datasets")
public class DatasetController {

    private final DatasetImportService datasetImportService;

    public DatasetController(DatasetImportService datasetImportService) {
        this.datasetImportService = datasetImportService;
    }

    @PostMapping("/import")
    public DatasetImportResponse importDataset(@RequestParam("file") MultipartFile file) {
        return datasetImportService.importFile(file);
    }
}
