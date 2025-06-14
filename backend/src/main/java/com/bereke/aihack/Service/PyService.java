package com.bereke.aihack.Service;

import com.bereke.aihack.dto.PyServiceResponseDto;
import com.bereke.aihack.dto.ResponseDto;
import com.bereke.aihack.util.Utils;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

@Service
public class PyService {

    private final Utils utils;

    public PyService(Utils utils) {
        this.utils = utils;
    }

    public ResponseDto analyzeResponse(PyServiceResponseDto dto, List<String> sanctionedNames) {
        if (dto == null) return null;

        List<String> reasons = new ArrayList<>();
        String country = dto.getForeignPartnerCountry().trim();

        // Проверка на РФ, РБ, Украина
        if (dto.getForeignPartnerCountry() != null) {

            if (country.equalsIgnoreCase("рк") || country.equalsIgnoreCase("rk")) {
                reasons.add("Валютные операции между резидентами РК запрещены.");
            } else {
                String partnerName = dto.getForeignPartnerName().toLowerCase();
                boolean isSanctionedCountry = country.equalsIgnoreCase("Россия") ||
                        country.equalsIgnoreCase("РФ") ||
                        country.equalsIgnoreCase("Беларусь") ||
                        country.equalsIgnoreCase("РБ") ||
                        country.equalsIgnoreCase("Украина");

                if (isSanctionedCountry && checkSanctionList(sanctionedNames, partnerName)) {
                    dto.setRelatedToRF_RB_UA(true);
                    reasons.add("Санкционный Банк");
                }
            }
        }

        // проверка валюты договора
        if (dto.getContractCurrency() != null) {
            String currencyCode = dto.getContractCurrency().trim().toUpperCase();

            if(currencyCode == null) {
                reasons.add("Нет валюты договора");
            }
            else {
                if (!utils.isValidCurrencyCode(currencyCode)) {
                    reasons.add("Неверный код валюты: " + currencyCode);
                }
            }
        }

        // Проверка даты договора
        if (dto.getContractDate() == null) {
            reasons.add("Нет даты договора");
        }

        // Проверка номера договора
        if (dto.getContractNumber() == null || dto.getContractNumber().isBlank()) {
            reasons.add("Нет номера договора");
        }

        // Проверка суммы договора
        if (dto.getContractAmount() == null || dto.getContractAmount().compareTo(BigDecimal.ZERO) <= 0) {
            reasons.add("Нет суммы договора");
        }

        // Проверка ТНВЭД кода
        if (country.equalsIgnoreCase("РФ") && (dto.getTnvedCode() == null || dto.getTnvedCode().isBlank())) {
            reasons.add("В договоре нет кода ТНВЭД");
        }

        // Проверка срока репатриации
        if (dto.getRepatriationPeriod() <= 0) {
            reasons.add("Нет сроков репатриации в договоре");
        }

        ResponseDto response = new ResponseDto();
        response.setIsOk(reasons.isEmpty());
        response.setReasonList(reasons);

        return response;
    }

    private boolean checkSanctionList(List<String> sanctionedNames, String partnerName) {
        for (String name : sanctionedNames) {
            if (partnerName.contains(name.toLowerCase())) {
                return true;
            }
        }
        return false;
    }

}
