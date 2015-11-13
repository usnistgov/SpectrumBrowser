package gov.nist.spectrumbrowser.client;

import java.util.logging.Level;
import java.util.logging.Logger;

import gov.nist.spectrumbrowser.client.SpectrumBrowser;
import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;

import com.google.gwt.user.client.ui.PasswordTextBox;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

/**
 * Screen for user to create a new login account
 * @author Julie Kub
 *
 */
public class UserCreateAccount implements SpectrumBrowserCallback<String> , SpectrumBrowserScreen {
	
	private VerticalPanel verticalPanel;
	private SpectrumBrowser spectrumBrowser;
	private PasswordTextBox passwordEntry;
	private PasswordTextBox passwordEntryConfirm;
	private TextBox emailEntry;
	private TextBox lastNameEntry;
	private TextBox firstNameEntry;
	private final SpectrumBrowserScreen loginScreen;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	public static final String LABEL = "Create Account";

	
	
	public UserCreateAccount(
			VerticalPanel verticalPanel, SpectrumBrowser spectrumBrowser, SpectrumBrowserScreen loginScreen) {
		logger.finer("UserCreateAccount");
		this.verticalPanel = verticalPanel;
		this.spectrumBrowser = spectrumBrowser;
		this.loginScreen = loginScreen;
				
	}
	
	class SubmitNewAccount implements ClickHandler {


			@Override
			public void onClick(ClickEvent event) {
				String firstName = "";
				String lastName = "";
				String password = "";
				String passwordConfirm = "";
				String emailAddress = "";
				try {
					firstName = firstNameEntry.getValue().trim();
					lastName = lastNameEntry.getValue().trim();
					password = passwordEntry.getValue();
					passwordConfirm = passwordEntryConfirm.getValue();
					emailAddress = emailEntry.getValue().trim();
					
				}
				catch (Throwable th) {
					//not a problem, since we will check for null's below.
				}
				//Just check that something was entered into each field, the server will check the rest.
				//By having the checks 'server side', we can have many clients & still get the same data validation checks.
				
				logger.finer("SubmitNewAccount: " + emailAddress);
				if (firstName == null || firstName.length() == 0) {
					Window.alert("First Name with at least one character is required.");
					return;
				}
				if (lastName == null || lastName.length() == 0) {
					Window.alert("Last Name with at least one character is required.");
					return;
				}

				if (emailAddress == null || emailAddress.length() == 0) {
					Window.alert("Email is required.");
					return;
				}

				if (password == null || password.length() == 0) {
					Window.alert("Password is required.");
					return;
				}
				if (passwordConfirm == null || passwordConfirm.length() == 0) {
					Window.alert("Re-typed password is required.");
					return;
				}
				if (password != passwordConfirm)
				{
					Window.alert("Password entries must match.");
					return;					
				}

				JSONObject jsonObject  = new JSONObject();
				jsonObject.put(Defines.ACCOUNT_EMAIL_ADDRESS, new JSONString(emailAddress));
				jsonObject.put(Defines.ACCOUNT_FIRST_NAME, new JSONString(firstName));
				jsonObject.put(Defines.ACCOUNT_LAST_NAME, new JSONString(lastName));
				jsonObject.put(Defines.ACCOUNT_PASSWORD, new JSONString(password));
				jsonObject.put(Defines.ACCOUNT_PRIVILEGE, new JSONString(Defines.USER_PRIVILEGE));

				spectrumBrowser.getSpectrumBrowserService().requestNewAccount(jsonObject.toString(), UserCreateAccount.this);
				verticalPanel.clear();
				loginScreen.draw();
					
				
			}
		

	}


	public void draw() {
		

		verticalPanel.clear();
		HTML title = new HTML("<h1>CAC Measured Spectrum Occupancy Database</h1><h2>Request Account </h2>");
		verticalPanel.add(title);
		
		Grid grid = new Grid(5,2);
		grid.setText(0, 0, "Email Address");
		emailEntry = new TextBox();
		emailEntry.setWidth("250px");
		grid.setWidget(0, 1, emailEntry);
		firstNameEntry = new TextBox();
		grid.setText(1, 0, "First Name");
		grid.setWidget(1,1,firstNameEntry);
		grid.setText(2,0, "Last Name");
		lastNameEntry = new TextBox();
		grid.setWidget(2, 1, lastNameEntry);
		grid.setText(3,0, "Password");
		passwordEntry = new PasswordTextBox();
		grid.setWidget(3, 1, passwordEntry);
		grid.setText(4,0, "Re-type password");
		passwordEntryConfirm = new PasswordTextBox();
		grid.setWidget(4, 1, passwordEntryConfirm);
		verticalPanel.add(grid);
			
		Grid buttonGrid = new Grid(1,2);
		verticalPanel.add(buttonGrid);

		Button buttonNewAccount = new Button("Submit");

		buttonNewAccount.addStyleName("sendButton");
		buttonGrid.setWidget(0,0,buttonNewAccount);
		buttonNewAccount.addClickHandler( new SubmitNewAccount());
		
		Button cancelButton = new Button("Cancel");
		buttonGrid.setWidget(0, 1, cancelButton);
		cancelButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				verticalPanel.clear();
				UserCreateAccount.this.loginScreen.draw();
			}});
	}

	@Override
	public void onSuccess(String result) {
		try {
			JSONObject jsonObject = JSONParser.parseLenient(result).isObject();
			String statusMessage = jsonObject.get(Defines.STATUS_MESSAGE).isString().stringValue();
			Window.alert(statusMessage);
		}
	    catch (Throwable th) {
		
		}
		
	}

	@Override
	public void onFailure(Throwable throwable) {
		logger.log(Level.SEVERE, "Error occured when contacting server in UserCreateAccount",throwable);
		Window.alert("Error occured contacting server in UserCreateAccount.");
		
	}

	@Override
	public String getLabel() {
		return LABEL;
	}

	@Override
	public String getEndLabel() {
		// TODO Auto-generated method stub
		return null;
	}
}
