package com.bereke.aihack.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

@Data
public class PyServiceResponseDto {
    private String contractNumber;
    @JsonFormat(pattern = "dd.MM.yyyy")
    private LocalDate contractDate;
    private String contractSubject;
    private BigDecimal contractAmount;
    private String contractCurrency;
    private String paymentCurrency;
    private int executionPeriod;
    private int paymentTerms;
    private String tnvedCode;
    private boolean liabilityClauses;
    private int repatriationPeriod;
    private String contractKNP;
    private String contractKVO;
    private boolean relatedToRF_RB_UA;  // проверка на санкции из excel файла
    private String foreignPartnerName;
    private String foreignPartnerBin;
    private String foreignPartnerCountry;
    private String foreignPartnerAccount;
    private String foreignPartnerBankSwift;
    private String foreignPartnerAddress;
    private boolean hasThirdParties;
}
