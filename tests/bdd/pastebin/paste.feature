@paste
Feature: Paste
  Inyoka provides also a module to create and manage pastes.


  Scenario: Users should be able to find a connection to the paste from the main page
    Given I am on the "main" page
     Then I should see a link to "paste.BASE_DOMAIN_NAME"


  Scenario Outline: Users should see a list of created pastes if they have the permission to do so
    Given I am "<username>"
      And I have the permission "pastebin.view_entry"
      And a "paste" with caption "BDD-TEST" exists
     When I use the "pastebin" and visit the "main" page
     Then I should see a "paste" with "BDD-TEST" in a list

    Examples:
      | username  |
      | anonymous |
      | BDD-User  |


  Scenario Outline: Users should see an exception if they shouldn't see entries
    Given I am "<username>"
     When I use the "pastebin" and visit the "main" page
     Then I should see a "403" exception

    Examples:
      | username  |
      | anonymous |
      | BDD-User  |


  Scenario Outline: Users should see the details of a paste if they have the permission
    Given I am "<username>"
      And a "paste" with caption "BDD-TEST" exists
      And I have the permission "pastebin.view_entry"
     When I open the "pastebin" in detail view
     Then I should see a title "BDD-TEST"
      And I should see elements with values
       | element      | value    |
       | entry_author | bdd      |
       | entry_code   | 1TEST    |

    Examples:
      | username  |
      | anonymous |
      | BDD-User  |

  Scenario Outline: Users shouldn't see the details of a paste if they haven't got the permission
    Given I am "<username>"
      And a "paste" with caption "BDD-TEST" exists
     When I open the "pastebin" in <view_type> view
     Then I should see a "403" exception

    Examples:
      | username  | view_type |
      | anonymous | detail    |
      | BDD-User  | detail    |
      | anonymous | raw       |
      | BDD-User  | raw       |


  Scenario Outline: If the paste isn't found a not found message should be returned
    Given I am "<username>"
      And I have the permission "<permission>"
     When I open the "pastebin" <view_type> view of "42"
     Then I should see a "not-found" message

    Examples:
      | username  | view_type | permission            |
      | anonymous | detail    | pastebin.view_entry   |
      | BDD-User  | detail    | pastebin.view_entry   |
      | anonymous | raw       | pastebin.view_entry   |
      | BDD-User  | raw       | pastebin.view_entry   |
      | BDD-User  | delete    | pastebin.delete_entry |


  Scenario Outline: User should be able to get the raw text of a paste
    Given I am "<username>"
      And a "paste" with caption "BDD-TEST" exists
      And I have the permission "pastebin.view_entry"
     When I open the "pastebin" in raw view
     Then I should see "TEST"

    Examples:
      | username  |
      | anonymous |
      | BDD-User  |


  Scenario: Users should be able to add pastes if they have the permission
    Given I am "BDD-User"
      And I have the permission "pastebin.add_entry"
      And I have the permission "pastebin.view_entry"
      And I use the "pastebin" and visit the "add" page
     When I fill out the form
       | field    | value |
       | id_title | title |
       | id_code  | text  |
     Then I should see a title "title"
      And I should see elements with values
       | element      | value    |
       | entry_author | BDD-User |
       | entry_code   | 1text    |


  Scenario: Anonymous should never be able to add a paste
    Given I am "anonymous"
      And I have the permission "pastebin.add_entry"
     When I use the "pastebin" and visit the "add" page
     Then I should be on the login page


  Scenario: Users should be able to delete pastes if they have the permission
    Given I am "BDD-User"
      And a "paste" with caption "BDD-TEST" exists
      And I have the permission "pastebin.view_entry"
      And I have the permission "pastebin.delete_entry"
     When I open the "pastebin" in delete view
      And I click on delete
     Then it should be successful


  Scenario: Users should be able to cancel the deletion of a paste
    Given I am "BDD-User"
      And a "paste" with caption "BDD-TEST" exists
      And I have the permission "pastebin.view_entry"
      And I have the permission "pastebin.delete_entry"
     When I open the "pastebin" in delete view
      And I click on cancel
     Then I should see canceled info
      And I should see a title "BDD-TEST"
      And I should see elements with values
       | element      | value    |
       | entry_author | bdd      |
       | entry_code   | 1TEST    |


  Scenario: Anonymous should never be able to delete a paste
    Given I am "anonymous"
      And I have the permission "pastebin.delete_entry"
      And a "paste" with caption "BDD-TEST" exists
     When I open the "pastebin" in delete view
     Then I should be on the login page
