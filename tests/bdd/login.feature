Feature: Logging in
  This feature tests the login to Inyoka.
  A user should be able to login if his account is active and denied access
  if not.


  Scenario: Open the login page
    Given I am on the login page
     Then I should see elements:
      | item        |
      | id_username |
      | id_password |


  Scenario: Login with a valid user
    Given I am on the login page
     When I enter the credentials:
      | username | password |
      | bdd_user | test     |
     Then it should be successful


  Scenario Outline: Login try with invalid credentials
    Given I am on the login page
     When I enter the credentials:
      | username   | password   |
      | <username> | <password> |
     Then it should fail

    Examples:
      | username | password |
      | bdd_user | invalid  |
      | invalid  | test     |


  Scenario Outline: Login try with an inactive  user
    Given I am on the login page
     When I enter the credentials:
      | username        | password |
      | <inactive_type> | test     |
     Then I should see information about
        """
        <inactive_type>
        """

    Examples:
      | inactive_type |
      | banned        |
      | inactive      |
      | deleted       |
