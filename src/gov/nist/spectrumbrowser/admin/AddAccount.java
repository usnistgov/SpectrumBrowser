package gov.nist.spectrumbrowser.admin;

import java.util.logging.Level;
import java.util.logging.Logger;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.PasswordTextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

public class AddAccount {
	
	private Admin admin;
	private AccountManagement accountManagement;
	private VerticalPanel verticalPanel;
	private TextBox emailEntry;
	private TextBox firstNameEntry;
	private TextBox lastNameEntry;
	private PasswordTextBox passwordEntry;
	private PasswordTextBox passwordEntryConfirm;
	private TextBox privilegeEntry;	
	private static boolean enablePasswordChecking = true;	
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

			if (emailAddress == null || emailAddress.length() == 0) {
				Window.alert("Email is required.");
				return;
			}
			//TODO: JEK: look at http://stackoverflow.com/questions/624581/what-is-the-best-java-email-address-validation-method
			// Better to use apache email validator than to use RegEx:
			if (!emailAddress 
					.matches("^[_A-Za-z0-9-]+(\\.[_A-Za-z0-9-]+)*@[A-Za-z0-9-]+(\\.[A-Za-z0-9-]+)*(\\.[A-Za-z]{2,})$")) {
				Window.alert("Please enter a valid email address.");
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
			/* The ITS password policy is:			
			 * At least 14 chars					
			 * Contains at least one digit					
			 * Contains at least one lower alpha char and one upper alpha char					
			 * Contains at least one char within a set of special chars (@#%$^ etc.)					
			 * Does not contain space, tab, etc. 
			 *
				^                 # start-of-string
				(?=.*[0-9])       # a digit must occur at least once
				(?=.*[a-z])       # a lower case letter must occur at least once
				(?=.*[A-Z])       # an upper case letter must occur at least once
				(?=.*[!@#$%^&+=])  # a special character must occur at least once
				.{12,}             # anything, at least 12 digits
				$                 # end-of-string
			 */

			// Password policy check disabled for debugging. Enable this for production.
			if (enablePasswordChecking && !password 
					.matches("((?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&+=])).{12,}$")) {
				Window.alert("Please enter a password with 1) at least 12 characters, 2) a digit, 3) an upper case letter, 4) a lower case letter, and 5) a special character(!@#$%^&+=).");
				return;
			}
			
			if (privilege == null || privilege.length() == 0) {
				Window.alert("Privilege is required.");
				return;
			}
			
			if (!privilege.equals("admin") && !privilege.equals("user")){
				Window.alert("Privilege must equal 'user' or 'admin'.");
				return;		
			}
			JSONObject jsonObject  = new JSONObject();
			jsonObject.put("emailAddress", new JSONString(emailAddress));
			jsonObject.put("firstName", new JSONString(firstName));
			jsonObject.put("lastName", new JSONString(lastName));
			jsonObject.put("password", new JSONString(password));
			jsonObject.put("privilege", new JSONString(privilege));
			Admin.getAdminService().addAccount(jsonObject.toString(), accountManagement);
				
			
		}
	

}
	
	public void draw() {
		verticalPanel.clear();
		HTML html = new HTML("<h2>Add account.</h2>");
		verticalPanel.add(html);
		if (!enablePasswordChecking) {
			HTML warning = new HTML("<h3>Debug Mode: password restrictions are off!</h3>");
			verticalPanel.add(warning);
		}
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

}
