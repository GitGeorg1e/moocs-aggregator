from __future__ import annotations

from sqlalchemy import Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class SimilarCourse(Base):
    __tablename__ = "similar_courses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        index=True,
    )
    similar_course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        index=True,
    )

    similarity: Mapped[float] = mapped_column(Float(), name="similarity")

    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "similar_course_id",
            name="uq_course_similar",
        ),
    )

    course = relationship(
        "Course",
        foreign_keys=[course_id],
        overlaps="similar_courses",
    )
    similar_course = relationship(
        "Course",
        foreign_keys=[similar_course_id],
        overlaps="similar_to",
    )
