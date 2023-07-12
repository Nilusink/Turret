"""
_target_classifier.py
24. April 2023

Remembers tracked objects and classifies by thread level

Author:
Nilusink
"""
import math


class TargetClassifier:
    _targets: list[int] = ...
    _target_boxes: dict[int, tuple[int, int, int, int]] = ...

    def __init__(self) -> None:
        self._targets = []
        self._target_boxes = {}

    def _update_record(self, boxes: list[tuple[int, int, int, int]]) -> None:
        """

        """
        n_last_targets = len(self._target_boxes)
        n_now_targets = len(boxes)

        last_centers: dict[int, tuple[float, float]] = {
            key: (pos[0] + pos[2] / 2, pos[1] + pos[3] / 2)
            for key, pos in self._target_boxes
        }

        now_centers: list[tuple[float, float]] = [
            (pos[0] + pos[2] / 2, pos[1] + pos[3] / 2)
            for pos in self._target_boxes
        ]

        # create a list with potential matches (how far the new target is away)
        last_matches: dict[int, list] = {tid: [] for tid in self._targets}
        for target_id in self._targets:
            center = last_centers[target_id]

            for box_center in now_centers:
                diff = center[0] - box_center[0], center[1] - box_center[1]
                i_diff = math.sqrt(diff[0] ** 2 + diff[1] ** 2)

                last_matches[target_id].append(i_diff)

        targets_to_match = list(range(n_now_targets))
        new_targets: dict[int, tuple[int, int, int, int]] = {
            key: ... for key in self._target_boxes.keys()
        }
        if n_now_targets == n_last_targets:
            for key, matches in last_matches:
                best_match = min([
                    match for i, match in enumerate(matches) if i in targets_to_match
                ])
                match = matches.index(best_match)
                targets_to_match.remove(match)

                new_targets[key] = boxes[match]

        elif n_last_targets < n_now_targets:
            for key, matches in last_matches:
                best_match = min([
                    match for i, match in enumerate(matches) if i in targets_to_match
                ])
                match = matches.index(best_match)
                targets_to_match.remove(match)

                new_targets[key] = boxes[match]

            for box in targets_to_match:
                target_id = max(new_targets.keys()) + 1
                new_targets[target_id] = boxes[box]

        elif n_last_targets > n_now_targets:
            for key, matches in last_matches:
                if len(targets_to_match) == 0:
                    continue

                best_match = min([
                    match for i, match in enumerate(matches) if i in targets_to_match
                ])
                match = matches.index(best_match)
                targets_to_match.remove(match)

                new_targets[key] = boxes[match]

        self._target_boxes = new_targets
        self._targets = list(self._target_boxes.keys())
