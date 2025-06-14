package com.bereke.aihack.util;

import org.springframework.stereotype.Component;

import java.util.Currency;

@Component
public class Utils {

    public boolean isValidCurrencyCode(String currencyCode) {
        try {
            Currency.getInstance(currencyCode.toUpperCase());
            return true;
        } catch (IllegalArgumentException e) {
            return false;
        }
    }

}
