package com.example.app.training.domain;

import java.util.Objects;
import java.util.Optional;

import com.example.app.error.domain.Assert;

/**
 * A course someone can take.
 *
 * <p>A class rather than a record: {@link #popularity} may be absent until the training
 * catalogue vendor supplies it, and a record's accessor cannot answer an {@code Optional} for
 * a component that may be absent — two ways to read one field is the trap a nullable field
 * plus an {@code Optional} accessor exists to avoid.
 */
public final class Course {

    private final CourseId id;
    private final Title title;

    /** Nullable until the training catalogue vendor supplies one, and answered as an Optional. */
    private final Popularity popularity;

    private Course(CourseBuilder builder) {
        Assert.notNull("id", builder.id);
        Assert.notNull("title", builder.title);

        this.id = builder.id;
        this.title = builder.title;
        this.popularity = builder.popularity;
    }

    public static CourseBuilder builder() {
        return new CourseBuilder();
    }

    public CourseId id() {
        return id;
    }

    public Title title() {
        return title;
    }

    /** Empty where the training catalogue has not supplied one yet. Never null. */
    public Optional<Popularity> popularity() {
        return Optional.ofNullable(popularity);
    }

    /**
     * This same course carrying the popularity handed in, leaving every other field alone.
     *
     * <p>A fill and never a clear: {@code popularity} is required, so there is no call of this
     * that ends with a course having less than it started with.
     */
    public Course withPopularity(Popularity popularity) {
        Assert.notNull("popularity", popularity);

        return builder().from(this).popularity(popularity).build();
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) {
            return true;
        }
        if (other == null || getClass() != other.getClass()) {
            return false;
        }

        Course course = (Course) other;

        return Objects.equals(id, course.id) && Objects.equals(title, course.title) && Objects.equals(popularity, course.popularity);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, title, popularity);
    }

    public static final class CourseBuilder {

        private CourseId id;
        private Title title;
        private Popularity popularity;

        private CourseBuilder() {
        }

        public CourseBuilder from(Course course) {
            this.id = course.id;
            this.title = course.title;
            this.popularity = course.popularity;

            return this;
        }

        public CourseBuilder id(CourseId id) {
            this.id = id;

            return this;
        }

        public CourseBuilder title(Title title) {
            this.title = title;

            return this;
        }

        public CourseBuilder popularity(Popularity popularity) {
            this.popularity = popularity;

            return this;
        }

        public Course build() {
            return new Course(this);
        }
    }
}
