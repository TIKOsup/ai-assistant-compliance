package com.bereke.aihack.Service;

import com.bereke.aihack.dto.PyServiceResponseDto;
import com.bereke.aihack.dto.ResponseDto;
import org.apache.poi.ss.usermodel.*;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

@Service
public class FileService {
    private final RestTemplate restTemplate = new RestTemplate();

    private final PyService pyService;

    public FileService(PyService pyService) {
        this.pyService = pyService;
    }

    public ResponseDto upload (MultipartFile file) throws IOException {
        String url = "http://pysvc:8091/upload";

        LinkedMultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", file);

        HttpHeaders httpHeaders  = new HttpHeaders();
        httpHeaders.setContentType(MediaType.MULTIPART_FORM_DATA);

        HttpEntity<LinkedMultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, httpHeaders);

        ResponseEntity<PyServiceResponseDto> response = restTemplate.exchange(
                url,
                HttpMethod.POST,
                requestEntity,
                PyServiceResponseDto.class
        );

        return pyService.analyzeResponse(
                response.getBody(),
                loadSanctionedCompanies());
    }

    private List<String> loadSanctionedCompanies() throws IOException {
        List<String> result = new ArrayList<>();
        try (InputStream is = new ClassPathResource("санционные списки США, ЕС, UK.xlsx").getInputStream()) {
            Workbook workbook = WorkbookFactory.create(is);
            for (int i = 0; i < workbook.getNumberOfSheets(); i++) {
                Sheet sheet = workbook.getSheetAt(i);
                for (Row row : sheet) {
                    Cell cell = row.getCell(1); // из столбца P_NAME
                    if (cell != null) {
                        result.add(getCellValueAsString(cell));
                    }
                }
            }
        }
        return result;
    }

    private String getCellValueAsString(Cell cell) {
        if (cell == null) return "";

        return switch (cell.getCellType()) {
            case STRING -> cell.getStringCellValue();
            case NUMERIC -> String.valueOf(cell.getNumericCellValue());
            case BOOLEAN -> String.valueOf(cell.getBooleanCellValue());
            case FORMULA -> cell.getCellFormula();
            case BLANK,_NONE,ERROR -> "";
            //case ERROR -> null;
        };
    }
}
