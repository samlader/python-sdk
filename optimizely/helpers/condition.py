# Copyright 2016, 2018-2020, Optimizely
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import numbers

from six import string_types

from . import validator
from .enums import CommonAudienceEvaluationLogs as audience_logs
from .enums import Errors, SemverType


class ConditionOperatorTypes(object):
    AND = 'and'
    OR = 'or'
    NOT = 'not'


class ConditionMatchTypes(object):
    EXACT = 'exact'
    EXISTS = 'exists'
    GREATER_THAN = 'gt'
    GREATER_THAN_OR_EQUAL = 'ge'
    LESS_THAN = 'lt'
    LESS_THAN_OR_EQUAL = 'le'
    SEMVER_EQ = 'semver_eq'
    SEMVER_GE = 'semver_ge'
    SEMVER_GT = 'semver_gt'
    SEMVER_LE = 'semver_le'
    SEMVER_LT = 'semver_lt'
    SUBSTRING = 'substring'


class CustomAttributeConditionEvaluator(object):
    """ Class encapsulating methods to be used in audience leaf condition evaluation. """

    CUSTOM_ATTRIBUTE_CONDITION_TYPE = 'custom_attribute'

    def __init__(self, condition_data, attributes, logger):
        self.condition_data = condition_data
        self.attributes = attributes or {}
        self.logger = logger

    def _get_condition_json(self, index):
        """ Method to generate json for logging audience condition.

        Args:
          index: Index of the condition.

        Returns:
          String: Audience condition JSON.
        """
        condition = self.condition_data[index]
        condition_log = {
            'name': condition[0],
            'value': condition[1],
            'type': condition[2],
            'match': condition[3],
        }

        return json.dumps(condition_log)

    def is_value_type_valid_for_exact_conditions(self, value):
        """ Method to validate if the value is valid for exact match type evaluation.

        Args:
          value: Value to validate.

        Returns:
          Boolean: True if value is a string, boolean, or number. Otherwise False.
        """
        # No need to check for bool since bool is a subclass of int
        if isinstance(value, string_types) or isinstance(value, (numbers.Integral, float)):
            return True

        return False

    def is_value_a_number(self, value):
        if isinstance(value, (numbers.Integral, float)) and not isinstance(value, bool):
            return True

        return False

    def exact_evaluator(self, index):
        """ Evaluate the given exact match condition for the user attributes.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user attribute value is equal (===) to the condition value.
            - False if the user attribute value is not equal (!==) to the condition value.
          None:
            - if the condition value or user attribute value has an invalid type.
            - if there is a mismatch between the user attribute type and the condition value type.
        """
        condition_name = self.condition_data[index][0]
        condition_value = self.condition_data[index][1]
        user_value = self.attributes.get(condition_name)

        if not self.is_value_type_valid_for_exact_conditions(condition_value) or (
                self.is_value_a_number(condition_value) and not validator.is_finite_number(condition_value)
        ):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index)))
            return None

        if not self.is_value_type_valid_for_exact_conditions(user_value) or not validator.are_values_same_type(
                condition_value, user_value
        ):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(self._get_condition_json(index), type(user_value), condition_name)
            )
            return None

        if self.is_value_a_number(user_value) and not validator.is_finite_number(user_value):
            self.logger.warning(
                audience_logs.INFINITE_ATTRIBUTE_VALUE.format(self._get_condition_json(index), condition_name)
            )
            return None

        return condition_value == user_value

    def exists_evaluator(self, index):
        """ Evaluate the given exists match condition for the user attributes.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean: True if the user attributes have a non-null value for the given condition,
                   otherwise False.
        """
        attr_name = self.condition_data[index][0]
        return self.attributes.get(attr_name) is not None

    def greater_than_evaluator(self, index):
        """ Evaluate the given greater than match condition for the user attributes.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user attribute value is greater than the condition value.
            - False if the user attribute value is less than or equal to the condition value.
          None: if the condition value isn't finite or the user attribute value isn't finite.
        """
        condition_name = self.condition_data[index][0]
        condition_value = self.condition_data[index][1]
        user_value = self.attributes.get(condition_name)

        if not validator.is_finite_number(condition_value):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index)))
            return None

        if not self.is_value_a_number(user_value):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(self._get_condition_json(index), type(user_value), condition_name)
            )
            return None

        if not validator.is_finite_number(user_value):
            self.logger.warning(
                audience_logs.INFINITE_ATTRIBUTE_VALUE.format(self._get_condition_json(index), condition_name)
            )
            return None

        return user_value > condition_value

    def greater_than_or_equal_evaluator(self, index):
        """ Evaluate the given greater than or equal to match condition for the user attributes.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user attribute value is greater than or equal to the condition value.
            - False if the user attribute value is less than the condition value.
            None: if the condition value isn't finite or the user attribute value isn't finite.
        """
        condition_name = self.condition_data[index][0]
        condition_value = self.condition_data[index][1]
        user_value = self.attributes.get(condition_name)

        if not validator.is_finite_number(condition_value):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index)))
            return None

        if not self.is_value_a_number(user_value):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(self._get_condition_json(index), type(user_value), condition_name)
            )
            return None

        if not validator.is_finite_number(user_value):
            self.logger.warning(
                audience_logs.INFINITE_ATTRIBUTE_VALUE.format(self._get_condition_json(index), condition_name)
            )
            return None

        return user_value >= condition_value

    def less_than_evaluator(self, index):
        """ Evaluate the given less than match condition for the user attributes.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user attribute value is less than the condition value.
            - False if the user attribute value is greater than or equal to the condition value.
          None: if the condition value isn't finite or the user attribute value isn't finite.
        """
        condition_name = self.condition_data[index][0]
        condition_value = self.condition_data[index][1]
        user_value = self.attributes.get(condition_name)

        if not validator.is_finite_number(condition_value):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index)))
            return None

        if not self.is_value_a_number(user_value):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(self._get_condition_json(index), type(user_value), condition_name)
            )
            return None

        if not validator.is_finite_number(user_value):
            self.logger.warning(
                audience_logs.INFINITE_ATTRIBUTE_VALUE.format(self._get_condition_json(index), condition_name)
            )
            return None

        return user_value < condition_value

    def less_than_or_equal_evaluator(self, index):
        """ Evaluate the given less than or equal to match condition for the user attributes.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user attribute value is less than or equal to the condition value.
            - False if the user attribute value is greater than the condition value.
          None: if the condition value isn't finite or the user attribute value isn't finite.
        """
        condition_name = self.condition_data[index][0]
        condition_value = self.condition_data[index][1]
        user_value = self.attributes.get(condition_name)

        if not validator.is_finite_number(condition_value):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index)))
            return None

        if not self.is_value_a_number(user_value):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(self._get_condition_json(index), type(user_value), condition_name)
            )
            return None

        if not validator.is_finite_number(user_value):
            self.logger.warning(
                audience_logs.INFINITE_ATTRIBUTE_VALUE.format(self._get_condition_json(index), condition_name)
            )
            return None

        return user_value <= condition_value

    def substring_evaluator(self, index):
        """ Evaluate the given substring match condition for the given user attributes.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the condition value is a substring of the user attribute value.
            - False if the condition value is not a substring of the user attribute value.
          None: if the condition value isn't a string or the user attribute value isn't a string.
        """
        condition_name = self.condition_data[index][0]
        condition_value = self.condition_data[index][1]
        user_value = self.attributes.get(condition_name)

        if not isinstance(condition_value, string_types):
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_VALUE.format(self._get_condition_json(index), ))
            return None

        if not isinstance(user_value, string_types):
            self.logger.warning(
                audience_logs.UNEXPECTED_TYPE.format(self._get_condition_json(index), type(user_value), condition_name)
            )
            return None

        return condition_value in user_value

    def semver_equal_evaluator(self, index):
        """ Evaluate the given semantic version equal match target version for the user version.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user version is equal (==) to the target version.
            - False if the user version is not equal (!=) to the target version.
          None:
            - if the user version value is not string type or is null.
        """
        return self.compare_user_version_with_target_version(index) == 0

    def semver_greater_than_evaluator(self, index):
        """ Evaluate the given semantic version greater than match target version for the user version.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user version is greater than the target version.
            - False if the user version is less than or equal to the target version.
          None:
            - if the user version value is not string type or is null.
        """
        return self.compare_user_version_with_target_version(index) > 0

    def semver_less_than_evaluator(self, index):
        """ Evaluate the given semantic version less than match target version for the user version.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user version is less than the target version.
            - False if the user version is greater than or equal to the target version.
          None:
            - if the user version value is not string type or is null.
        """
        return self.compare_user_version_with_target_version(index) < 0

    def semver_less_than_or_equal_evaluator(self, index):
        """ Evaluate the given semantic version less than or equal to match target version for the user version.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user version is less than or equal to the target version.
            - False if the user version is greater than the target version.
          None:
            - if the user version value is not string type or is null.
        """
        return self.compare_user_version_with_target_version(index) <= 0

    def semver_greater_than_or_equal_evaluator(self, index):
        """ Evaluate the given semantic version greater than or equal to match target version for the user version.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user version is greater than or equal to the target version.
            - False if the user version is less than the target version.
          None:
            - if the user version value is not string type or is null.
        """
        return self.compare_user_version_with_target_version(index) >= 0

    def split_semantic_version(self, target):
        """ Method to split the given version.

        Args:
          target: Given version.

        Returns:
          List:
            - The array of version split into smaller parts i.e major, minor, patch etc
          Exception:
            - if the given version is invalid in format
        """
        target_prefix = target
        target_suffix = ""
        target_parts = []

        if self.has_white_space(target):
            self.logger.warning(Errors.INVALID_ATTRIBUTE_FORMAT)
            return None

        if self.is_pre_release(target):
            target_parts = target.split(SemverType.IS_PRE_RELEASE)
        elif self.is_build(target):
            target_parts = target.split(SemverType.IS_BUILD)

        if target_parts:
            if len(target_parts) < 1:
                self.logger.warning(Errors.INVALID_ATTRIBUTE_FORMAT)
                return None
            target_prefix = str(target_parts[0])
            target_suffix = target_parts[1:]

        dot_count = target_prefix.count(".")
        if dot_count > 2:
            self.logger.warning(Errors.INVALID_ATTRIBUTE_FORMAT)
            return None

        target_version_parts = target_prefix.split(".")
        if len(target_version_parts) != dot_count + 1:
            self.logger.warning(Errors.INVALID_ATTRIBUTE_FORMAT)
            return None
        for part in target_version_parts:
            if not part.isdigit():
                self.logger.warning(Errors.INVALID_ATTRIBUTE_FORMAT)
                return None

        if target_suffix:
            target_version_parts.extend(target_suffix)
        return target_version_parts

    def is_pre_release(self, target):
        """ Method to check if the given version contains "-"

        Args:
          target: Given version in string.

        Returns:
          Boolean:
            - True if the given version does contain "-"
            - False if it doesn't
        """
        return SemverType.IS_PRE_RELEASE in target

    def is_patch_pre_release(self, idx, idx_value):
        return idx == SemverType.PATCH_INDEX and idx_value in SemverType.IS_PATCH_PRE_RELEASE

    def is_build(self, target):
        """ Method to check if the given version contains "+"

        Args:
          target: Given version in string.

        Returns:
          Boolean:
            - True if the given version does contain "+"
            - False if it doesn't
        """
        return SemverType.IS_BUILD in target

    def has_white_space(self, target):
        """ Method to check if the given version contains " " (white space)

        Args:
          target: Given version in string.

        Returns:
          Boolean:
            - True if the given version does contain " "
            - False if it doesn't
        """
        return SemverType.HAS_WHITE_SPACE in target

    def compare_user_version_with_target_version(self, index):
        """ Method to compare user version with target version.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Int:
            -  0 if user version is equal to target version.
            -  1 if user version is greater than target version.
            - -1 if user version is less than target version or, in case of exact string match, doesn't match the target
            version.
          None:
            - if the user version value is not string type or is null.
        """
        condition_name = self.condition_data[index][0]
        target_version = self.condition_data[index][1]
        user_version = self.attributes.get(condition_name)

        target_version_parts = self.split_semantic_version(target_version)
        user_version_parts = self.split_semantic_version(user_version)
        user_version_parts_len = len(user_version_parts)

        for (idx, _) in enumerate(target_version_parts):
            if user_version_parts_len <= idx:
                return 1 if self.is_pre_release(target_version) else -1
            elif not user_version_parts[idx].isdigit():
                if user_version_parts[idx] < target_version_parts[idx]:
                    return -1
                elif user_version_parts[idx] > target_version_parts[idx]:
                    return 1
            else:
                user_version_part = int(user_version_parts[idx])
                target_version_part = int(target_version_parts[idx])
                if user_version_part > target_version_part:
                    return 1
                elif user_version_part < target_version_part:
                    return -1
        if self.is_pre_release(user_version) and not self.is_pre_release(target_version):
            return -1
        return 0

    EVALUATORS_BY_MATCH_TYPE = {
        ConditionMatchTypes.EXACT: exact_evaluator,
        ConditionMatchTypes.EXISTS: exists_evaluator,
        ConditionMatchTypes.GREATER_THAN: greater_than_evaluator,
        ConditionMatchTypes.LESS_THAN: less_than_evaluator,
        ConditionMatchTypes.SEMVER_EQ: semver_equal_evaluator,
        ConditionMatchTypes.SEMVER_GE: semver_greater_than_or_equal_evaluator,
        ConditionMatchTypes.SEMVER_GT: semver_greater_than_evaluator,
        ConditionMatchTypes.SEMVER_LE: semver_less_than_or_equal_evaluator,
        ConditionMatchTypes.SEMVER_LT: semver_less_than_evaluator,
        ConditionMatchTypes.SUBSTRING: substring_evaluator,
        ConditionMatchTypes.LESS_THAN_OR_EQUAL: less_than_or_equal_evaluator,
        ConditionMatchTypes.GREATER_THAN_OR_EQUAL: greater_than_or_equal_evaluator,
    }

    def evaluate(self, index):
        """ Given a custom attribute audience condition and user attributes, evaluate the
        condition against the attributes.

        Args:
          index: Index of the condition to be evaluated.

        Returns:
          Boolean:
            - True if the user attributes match the given condition.
            - False if the user attributes don't match the given condition.
          None: if the user attributes and condition can't be evaluated.
        """

        if self.condition_data[index][2] != self.CUSTOM_ATTRIBUTE_CONDITION_TYPE:
            self.logger.warning(audience_logs.UNKNOWN_CONDITION_TYPE.format(self._get_condition_json(index)))
            return None

        condition_match = self.condition_data[index][3]
        if condition_match is None:
            condition_match = ConditionMatchTypes.EXACT

        if condition_match not in self.EVALUATORS_BY_MATCH_TYPE:
            self.logger.warning(audience_logs.UNKNOWN_MATCH_TYPE.format(self._get_condition_json(index)))
            return None

        if condition_match != ConditionMatchTypes.EXISTS:
            attribute_key = self.condition_data[index][0]
            if attribute_key not in self.attributes:
                self.logger.debug(
                    audience_logs.MISSING_ATTRIBUTE_VALUE.format(self._get_condition_json(index), attribute_key)
                )
                return None

            if self.attributes.get(attribute_key) is None:
                self.logger.debug(
                    audience_logs.NULL_ATTRIBUTE_VALUE.format(self._get_condition_json(index), attribute_key)
                )
                return None

        return self.EVALUATORS_BY_MATCH_TYPE[condition_match](self, index)


class ConditionDecoder(object):
    """ Class which provides an object_hook method for decoding dict
    objects into a list when given a condition_decoder. """

    def __init__(self, condition_decoder):
        self.condition_list = []
        self.index = -1
        self.decoder = condition_decoder

    def object_hook(self, object_dict):
        """ Hook which when passed into a json.JSONDecoder will replace each dict
        in a json string with its index and convert the dict to an object as defined
        by the passed in condition_decoder. The newly created condition object is
        appended to the conditions_list.

        Args:
          object_dict: Dict representing an object.

        Returns:
          An index which will be used as the placeholder in the condition_structure
        """
        instance = self.decoder(object_dict)
        self.condition_list.append(instance)
        self.index += 1
        return self.index


def _audience_condition_deserializer(obj_dict):
    """ Deserializer defining how dict objects need to be decoded for audience conditions.

    Args:
      obj_dict: Dict representing one audience condition.

    Returns:
      List consisting of condition key with corresponding value, type and match.
    """
    return [
        obj_dict.get('name'),
        obj_dict.get('value'),
        obj_dict.get('type'),
        obj_dict.get('match'),
    ]


def loads(conditions_string):
    """ Deserializes the conditions property into its corresponding
    components: the condition_structure and the condition_list.

    Args:
      conditions_string: String defining valid and/or conditions.

    Returns:
      A tuple of (condition_structure, condition_list).
      condition_structure: nested list of operators and placeholders for operands.
      condition_list: list of conditions whose index correspond to the values of the placeholders.
    """
    decoder = ConditionDecoder(_audience_condition_deserializer)

    # Create a custom JSONDecoder using the ConditionDecoder's object_hook method
    # to create the condition_structure as well as populate the condition_list
    json_decoder = json.JSONDecoder(object_hook=decoder.object_hook)

    # Perform the decoding
    condition_structure = json_decoder.decode(conditions_string)
    condition_list = decoder.condition_list

    return (condition_structure, condition_list)
