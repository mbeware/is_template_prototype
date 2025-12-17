# Flow Connector Widgets

## connector

### connector.createPage("service") -> page object

## Menu

### connector.createMenuWidget() -> menuWidget object

### menuWidget.updateFunction(function) -> updated menuWidget object

update fonctionpourrait plutot etre la route?

The function takes dictonnary parameter and returns a dictionary with keys 'title' and 'choices', where 'choices' is a list of dictionaries with keys 'label' and 'description' and 'data'.

## menuWidget.handleResponse(function) -> triggered when a user selects an option from the menu

The function takes one parameter 'data' which is the 'data' value of the selected choice.

## TextInput

### connector.createTextInputWidget(title="\<title\>", prompt="\<prompt\>", default="\<default_value\>", button="\<button_text\>", secret=\<boolean\>) -> textInputWidget object

title: string - the title of the text input widget. can be omitted.
prompt: string - the prompt shown to the user. can be omitted.
value: string - the default value shown in the input field. can be omitted.
button: string - the text shown on the submit button.
secret: string - if "true", the input will be masked (like a password). default is "false".

### TextInputWidget.updateFunction(function) -> updated TextInputWidget object

The function takes dictonnary parameter and returns a dictionary. keys of the dictionnary are the same as the parameters of createTextInputWidget

## textBlock

### connector.createTextBlockWidget() -> textBlockWidget object

### textBlockWidget.updateFunction(function) -> updated textBlockWidget object

the function takes no parameters and returns a string.

## Page

### page.addWidget(widget) -> updated page object


