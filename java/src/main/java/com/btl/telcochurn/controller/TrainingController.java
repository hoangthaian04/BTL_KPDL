package com.btl.telcochurn.controller;

import com.btl.telcochurn.dto.TrainingResponse;
import com.btl.telcochurn.service.TrainingService;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/models")
public class TrainingController {

    private final TrainingService trainingService;

    public TrainingController(TrainingService trainingService) {
        this.trainingService = trainingService;
    }

    @PostMapping("/train")
    public TrainingResponse train() {
        return trainingService.train();
    }
}
