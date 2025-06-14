package com.bereke.aihack.controller;

import com.bereke.aihack.Service.FileService;
import com.bereke.aihack.dto.ResponseDto;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

@RestController
@RequestMapping("/file")
public class FileController {

    private final FileService fileService;

    public FileController(FileService fileService) {
        this.fileService = fileService;
    }

    @PostMapping(consumes = "multipart/form-data")
    public ResponseDto uploadFile(
            @RequestParam("file") MultipartFile file
    ) throws IOException {
        return fileService.upload(file);
    }
}
