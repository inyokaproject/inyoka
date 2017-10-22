Feature: Logging in
  This feature tests the login to Inyoka.


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

