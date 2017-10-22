Feature: Password forgotten
  A user should be able to help himself if he has forgotten his password.


  Scenario: The user has forgotten the password so he should be able to see the forgotten link
    Given I am on the login page
    Then I should see a link to:
      | link_location |
      | lost_password |
