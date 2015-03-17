package gov.nist.spectrumbrowser.admin;

import java.util.logging.Level;
import java.util.logging.Logger;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.PasswordTextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowser;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

public class AddAccount implements
SpectrumBrowserCallback<String>{
	
	private Admin admin;
	private AccountManagement accountManagement;
	private VerticalPanel verticalPanel;
	private TextBox emailEntry;
	private TextBox firstNameEntry;
	private TextBox lastNameEntry;
	private PasswordTextBox passwordEntry;
	private PasswordTextBox passwordEntryConfirm;
	private TextBox privilegeEntry;	
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	
	public AddAccount(Admin admin, AccountManagement accountManagement, VerticalPanel verticalPanel) {
		this.admin = admin;
		this.accountManagement = accountManagement;
		this.verticalPanel = verticalPanel;
	}
	
	class SubmitNewAccount implements ClickHandler {


		@Override
		public void onClick(ClickEvent event) {
			String firstName = "";
			String lastName = "";
			String password = "";
			String passwordConfirm = "";
			String emailAddress =  "";
			String privilege = "";
			try {
			   emailAddress = emailEntry.getValue().trim();
			   firstName = firstNameEntry.getValue().trim();
			   lastName = lastNameEntry.getValue().trim();
			   password = passwordEntry.getValue();
			   passwordConfirm = passwordEntryConfirm.getValue();
			   privilege = privilegeEntry.getValue().trim().toLowerCase();
			}
			catch (Throwable th) {
				//not a problem, since we will check for null's below.
			}

			//Just check that something was entered into each field, the server will check the rest.
			//By having the checks 'server side', we can have many clients & still get the same data validation checks.
			if (emailAddress == null || emailAddress.length() == 0) {
				Window.alert("Email is required.");
				return;
			}

			if (firstName == null || firstName.length() == 0) {
				Window.alert("First Name with at least one character is required.");
				return;
			}
			if (lastName == null || lastName.length() == 0) {
				Window.alert("Last Name with at least one character is required.");
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

			
			if (privilege == null || privilege.length() == 0) {
				Window.alert("Privilege is required.");
				return;
			}

			JSONObject jsonObject  = new JSONObject();
			jsonObject.put(AbstractSpectrumBrowser.ACCOUNT_EMAIL_ADDRESS, new JSONString(emailAddress));
			jsonObject.put(AbstractSpectrumBrowser.ACCOUNT_FIRST_NAME, new JSONString(firstName));
			jsonObject.put(AbstractSpectrumBrowser.ACCOUNT_LAST_NAME, new JSONString(lastName));
			jsonObject.put(AbstractSpectrumBrowser.ACCOUNT_PASSWORD, new JSONString(password));
			jsonObject.put(AbstractSpectrumBrowser.ACCOUNT_PRIVILEGE, new JSONString(privilege));
			Admin.getAdminService().addAccount(jsonObject.toString(), accountManagement);			
		}
	

}
	
	public void draw() {
		verticalPanel.clear();
		HTML html = new HTML("<h2>Add account</h2>");
		verticalPanel.add(html);
		Grid grid = new Grid(6,2);
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
		grid.setText(5,0, "Privilege (admin/user)");
		privilegeEntry = new TextBox();
		grid.setWidget(5, 1, privilegeEntry);
		verticalPanel.add(grid);
		HorizontalPanel buttonPanel = new HorizontalPanel();
		Button applyButton = new Button("Apply");
		applyButton.addClickHandler( new SubmitNewAccount());
		buttonPanel.add(applyButton);
		Button cancelButton = new Button("Cancel");
		cancelButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				accountManagement.draw();				
			}});
		buttonPanel.add(cancelButton);
		
		Button logoffButton = new Button("Log Off");
		logoffButton.addClickHandler( new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}});
		buttonPanel.add(logoffButton);
		
		verticalPanel.add(buttonPanel);
		
	}
	
	@Override
	public void onSuccess(String result) {
		try {
			JSONValue jsonValue = JSONParser.parseLenient(result);
			String serverStatus = jsonValue.isObject().get("status").isString().stringValue();
			String serverStatusMessage = jsonValue.isObject().get("statusMessage").isString().stringValue();
			logger.finer("serverStatus " + serverStatus);
			logger.finer("serverStatusMessage " + serverStatusMessage);
			
			if (serverStatus != "OK"){
				logger.finer("serverStatus in add account: " + serverStatus);
				Window.alert(serverStatusMessage);
			}
			else{
				new AccountManagement(this.admin).draw();
			}
				

		} catch (Throwable th) {
			Window.alert("Error parsing returned JSON");
			logger.log(Level.SEVERE, "Problem parsing JSON", th);
		}
	}

	@Override
	public void onFailure(Throwable throwable) {
		Window.alert("Error communicating with server in Add Account");
		logger.log(Level.SEVERE, "Error communicating with server", throwable);
		admin.logoff();
	}

}
