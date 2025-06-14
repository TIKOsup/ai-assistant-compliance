package com.bereke.aihack.dto;

import lombok.Data;

import java.util.List;

@Data
public class ResponseDto {
    Boolean isOk;
    List<String> reasonList;
}
