package com.example.app.training.domain;

import com.example.app.error.domain.Assert;

/**
 * How well-regarded a course is, on the training catalogue vendor's own 0-100 scale. Absent
 * until that vendor supplies it — nothing here computes one.
 */
public record Popularity(int value) {

    public Popularity {
        Assert.field("popularity", value).positive().max(100);
    }
}
