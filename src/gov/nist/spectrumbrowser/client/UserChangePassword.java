package gov.nist.spectrumbrowser.client;

import java.util.logging.Level;
import java.util.logging.Logger;

import gov.nist.spectrumbrowser.client.LoginScreen;
import gov.nist.spectrumbrowser.client.SpectrumBrowser;
import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowser;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import com.google.gwt.core.client.Scheduler;
import com.google.gwt.dom.client.HeadingElement;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.PasswordTextBox;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

/**
 * Screen for user to create a new login account
 * @author Julie Kub
 *
 */
public class UserChangePassword implements SpectrumBrowserCallback<String> , SpectrumBrowserScreen {
	
	private VerticalPanel verticalPanel;
	private SpectrumBrowser spectrumBrowser;
	private PasswordTextBox oldPasswordEntry;
	private PasswordTextBox passwordEntry;
	private PasswordTextBox passwordEntryConfirm;
	private TextBox emailEntry;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	public static final String LOGIN_LABEL = "Login";
	public static final String LABEL  = "Create Account";
	
	private static boolean enablePasswordChecking = false;
	
	
	
	public UserChangePassword(
			VerticalPanel verticalPanel, SpectrumBrowser spectrumBrowser) {
		logger.finer("UserCreateAccount");
		this.verticalPanel = verticalPanel;
		this.spectrumBrowser = spectrumBrowser;
				
	}
	
	class SubmitChangePassword implements ClickHandler {


			@Override
			public void onClick(ClickEvent event) {
				String oldPassword = oldPasswordEntry.getValue();				
				String password = passwordEntry.getValue();
				String passwordConfirm = passwordEntryConfirm.getValue();
				String emailAddress = emailEntry.getValue();
				logger.finer("SubmitNewAccount: " + emailAddress);
				if (emailAddress == null || emailAddress.length() == 0) {
					Window.alert("Email is required.");
					return;
				}
				if (oldPassword == null || oldPassword.length() == 0) {
					Window.alert("Current password is required.");
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


				/* Sadly, this password policy will drive anybody to tears and reduce the 
				 * value of the system. However, it is what it is:
				 * The password policy is:			
				 * At least 14 chars					
				 * Contains at least one digit					
				 * Contains at least one lower alpha char and one upper alpha char					
				 * Contains at least one char within a set of special chars (@#%$^ etc.)					
				 * Does not contain space, tab, etc. Yeah. Osama bin Laden made us do it! 
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
				if (emailAddress.matches("(.*(\\.gov|\\.mil|\\.GOV|\\.MIL)+)$")){
					spectrumBrowser.getSpectrumBrowserService().createNewAccount(firstName,lastName, emailAddress,
							password,AbstractSpectrumBrowser.getBaseUrlAuthority(),UserCreateAccount.this);
					Window.alert("Please check your email for notification");
					return;
				}
				else {
					//TODO: JEK: if not .gov/.mil, email admin to approve/deny account creation
					Window.alert("not .gov or .mil - your request has been forwarded to admin. Check your mail for notification.");
				}
				
					
				
			};
		

	}


	public void draw() {
		

		verticalPanel.clear();
		HTML title = new HTML("<h2>Change Password</h2>");
		verticalPanel.add(title);
				
		HorizontalPanel emailField = new HorizontalPanel();
		Label emailLabel = new Label("Email Address");
		emailLabel.setWidth("150px");
		emailField.add(emailLabel);
		emailEntry = new TextBox();
		emailEntry.setWidth("150px");
		emailEntry.setText("");
		emailField.add(emailEntry);
		verticalPanel.add(emailField);
		
		HorizontalPanel oldPasswordField = new HorizontalPanel();
		Label oldPasswordLabel = new Label("Current Password");
		oldPasswordLabel.setWidth("150px");
		oldPasswordField.add(oldPasswordLabel);
		oldPasswordEntry = new PasswordTextBox();
		oldPasswordEntry.setWidth("150px");
		oldPasswordEntry.setText("");
		oldPasswordField.add(oldPasswordEntry);
		verticalPanel.add(oldPasswordField);
		
		HorizontalPanel passwordField = new HorizontalPanel();
		Label passwordLabel = new Label("Choose a Password (at least 12 chars, uppercase, lowercase, numeric, and special character(!@#$%^&+=))");
		passwordLabel.setWidth("150px");
		passwordField.add(passwordLabel);
		passwordEntry = new PasswordTextBox();
		passwordEntry.setWidth("150px");
		passwordEntry.setText("");
		passwordField.add(passwordEntry);
		verticalPanel.add(passwordField);
		
		HorizontalPanel passwordFieldConfirm = new HorizontalPanel();
		Label passwordLabelConfirm = new Label("Re-type password");
		passwordLabelConfirm.setWidth("150px");
		passwordFieldConfirm.add(passwordLabelConfirm);
		passwordEntryConfirm = new PasswordTextBox();
		passwordEntryConfirm.setWidth("150px");
		passwordEntryConfirm.setText("");
		passwordFieldConfirm.add(passwordEntryConfirm);
		verticalPanel.add(passwordFieldConfirm);
		
		Button buttonSubmit = new Button("Submit");
		buttonSubmit.addStyleName("sendButton");
		verticalPanel.add(buttonSubmit);
		buttonSubmit.addClickHandler( new SubmitChangePassword());
	}

	@Override
	public void onSuccess(String result) {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void onFailure(Throwable throwable) {
		// TODO Auto-generated method stub
		
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
