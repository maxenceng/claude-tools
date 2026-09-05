package com.example.app.training.domain;

import com.example.app.error.domain.Assert;

/** What a course is called. */
public record Title(String value) {

    public Title {
        Assert.field("title", value).notBlank();
    }
}
