package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.PasswordTextBox;
import com.google.gwt.user.client.ui.PopupPanel;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

public class LoginScreen implements SpectrumBrowserScreen {
	VerticalPanel verticalPanel;
	static Logger logger = Logger.getLogger("SpectrumBrowser");
	PasswordTextBox passwordEntry;
	TextBox nameEntry;
	String locationName;
	PopupPanel popupPanel = new PopupPanel();
	String sessionToken;
	private String LABEL = "Login >>";
	private String END_LABEL = "Login";

	/**
	 * Create a remote service proxy to talk to the server-side Greeting
	 * service.
	 */
	private SpectrumBrowser spectrumBrowser;

	/**
	 * The message displayed to the user when the server cannot be reached or
	 * returns an error.
	 */
	private static final String HEADING_TEXT = "CAC Measured Spectrum Occupancy Database";

	/**
	 * The welcome text. This should be defined as a resource in another file
	 * For now we hard code it here.
	 */
	private static final String WELCOME_TEXT =   "Enter User Name and password to proceed or request an account to begin using the system.";

	class SendNamePasswordToServer implements ClickHandler {

		@Override
		public void onClick(ClickEvent clickEvent) {
			String name = nameEntry.getValue();
			String password = passwordEntry.getValue();
			logger.finer("SendNamePasswordToServer: " + name);
			if (name == null || name.length() == 0) {
				Window.alert("Name is mandatory");
				return;
			}

			getSpectrumBrowserService().authenticate(name, password, "user",
					new SpectrumBrowserCallback<String>() {

						@Override
						public void onFailure(Throwable errorTrace) {
							logger.log(Level.SEVERE,
									"Error sending request to the server",
									errorTrace);
							Window.alert("Error communicating with the server.");

						}

						@Override
						public void onSuccess(String result) {
							JSONValue jsonValue = JSONParser
									.parseStrict(result);
							JSONObject jsonObject = jsonValue.isObject();
							String res = jsonObject.get("status").isString()
									.stringValue();
							if (res.startsWith("OK")) {
								sessionToken = jsonObject.get("sessionId")
										.isString().stringValue();
								spectrumBrowser.setSessionToken(sessionToken);
								spectrumBrowser.setUserLoggedIn(true);
								new SpectrumBrowserShowDatasets(
										spectrumBrowser, verticalPanel);
							} else {
								Window.alert("Username or Password is incorrect. Please try again");
							}
						}
					});

		}

	}

	public String getLabel() {
		return LABEL;
	}

	public String getEndLabel() {
		return END_LABEL;
	}

	/**
	 * Display the error message and put up the login screen again.
	 * 
	 * @param errorMessage
	 */
	public void displayError(String errorMessage) {
		Window.alert(errorMessage);
		// logoff();

	}

	SpectrumBrowserServiceAsync getSpectrumBrowserService() {
		return spectrumBrowser.getSpectrumBrowserService();
	}

	class SubmitChangePassword implements ClickHandler {

		@Override
		public void onClick(ClickEvent event) {
			String emailAddress = nameEntry.getValue();
			if (emailAddress == null || emailAddress.length() == 0) {
				Window.alert("Email is required to change your password.");
				return;
			}
			// TODO: JEK: add a check here to see if the emailAddress is for a
			// valid user
			spectrumBrowser.getSpectrumBrowserService()
					.emailChangePasswordUrlToUser(
							SpectrumBrowser.getSessionToken(),
							SpectrumBrowser.getBaseUrlAuthority(),
							emailAddress,
							new SpectrumBrowserCallback<String>() {

								@Override
								public void onSuccess(String result) {
									JSONValue jsonValue = JSONParser
											.parseLenient(result);
									String status = jsonValue.isObject()
											.get("status").isString()
											.stringValue();
									if (status.equals("OK")) {
										Window.alert("Please check your email for a link to enter a new password.");
									} else {
										Window.alert("Error sending an email with a new password link.");
									}

								}

								@Override
								public void onFailure(Throwable throwable) {
									Window.alert("Error communicating with server");

								}

							});

		}
	}

	/**
	 * This is the entry point method.
	 */
	public void draw() {
		verticalPanel.clear();
		logger.log(Level.INFO, "Base URL " + SpectrumBrowser.getBaseUrl());
		verticalPanel
				.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		verticalPanel.setStyleName("loginPanel");
		verticalPanel.setSpacing(20);
		HTML headingText = new HTML("<H1>" + HEADING_TEXT + "<H1>");
		verticalPanel.add(headingText);
		HTML welcomeText = new HTML("<H2>" + WELCOME_TEXT + "</H2>");
		verticalPanel.add(welcomeText);
		HorizontalPanel nameField = new HorizontalPanel();
		// Should use internationalization. for now just hard code it.
		Label nameLabel = new Label("Email");
		nameLabel.setWidth("150px");
		nameField.add(nameLabel);
		nameEntry = new TextBox();
		nameEntry.setText("guest@nist.gov");
		nameEntry.setWidth("150px");
		nameField.add(nameEntry);
		verticalPanel.add(nameField);

		HorizontalPanel passwordField = new HorizontalPanel();
		Label passwordLabel = new Label("Password");
		passwordLabel.setWidth("150px");
		passwordField.add(passwordLabel);
		passwordEntry = new PasswordTextBox();
		passwordEntry.setWidth("150px");
		passwordField.add(passwordLabel);
		passwordField.add(passwordEntry);
		verticalPanel.add(passwordField);

		// Add the nameField and sendButton to the RootPanel
		// Use RootPanel.get() to get the entire body element

		// Focus the cursor on the name field when the app loads
		nameEntry.setFocus(true);
		nameEntry.selectAll();

		Grid buttonGrid = new Grid(1, 4);
		Button sendButton = new Button("Sign in");
		// We can add style names to widgets
		verticalPanel
				.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		sendButton.addStyleName("sendButton");
		sendButton.addClickHandler(new SendNamePasswordToServer());
		buttonGrid.setWidget(0,0,sendButton);
		Button createAccount = new Button("Request Account");
		createAccount.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				new UserCreateAccount(verticalPanel,LoginScreen.this.spectrumBrowser, LoginScreen.this).draw();
			}
		});

		buttonGrid.setWidget(0, 1, createAccount);

		Button forgotPasswordButton = new Button("Forgot Password");
		buttonGrid.setWidget(0, 2, forgotPasswordButton);

		Button changePasswordButton = new Button("Change Password");
		buttonGrid.setWidget(0, 3, changePasswordButton);

		verticalPanel.add(buttonGrid);
	}

	public void logoff() {

		getSpectrumBrowserService().logOff(
				new SpectrumBrowserCallback<String>() {

					@Override
					public void onFailure(Throwable caught) {
						draw();
					}

					@Override
					public void onSuccess(String result) {
						// TODO Auto-generated method stub
						draw();
					}
				});
	}

	public LoginScreen(SpectrumBrowser spectrumBrowser) {
		verticalPanel = new VerticalPanel();
		RootPanel.get().add(verticalPanel);
		this.spectrumBrowser = spectrumBrowser;
	}

}
