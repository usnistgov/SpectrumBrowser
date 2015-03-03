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
import com.google.gwt.user.client.ui.Image;
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

			getSpectrumBrowserService().authenticate(name.trim(), password, "user",
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
							if (res.equals("OK")) {
								sessionToken = jsonObject.get("sessionId")
										.isString().stringValue();
								spectrumBrowser.setSessionToken(sessionToken);
								spectrumBrowser.setUserLoggedIn(true);
								new SpectrumBrowserShowDatasets(
										spectrumBrowser, verticalPanel);
							} 
							else if ( res.equals("INVALUSER")) {
								Window.alert("Invalid email and/or password. Please try again.");	
							}
							else if ( res.equals("INVALSESSION")) {
								Window.alert("Failed to generate a valid session key.");	
							}
							else if ( res.equals("ACCLOCKED")) {
								Window.alert("Your account is locked. Please reset your password.");	
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
		// HTML headingText = new HTML("<H1>" + HEADING_TEXT + "<H1>");
		// verticalPanel.add(headingText);
		HorizontalPanel nameField = new HorizontalPanel();
		// Should use internationalization. for now just hard code it.
		Label nameLabel = new Label("Email");
		nameLabel.setWidth("150px");
		nameField.add(nameLabel);
		nameEntry = new TextBox();
		nameEntry.setText("guest@nist.gov");
		nameEntry.setWidth("250px");
		nameField.add(nameEntry);
		verticalPanel.add(nameField);

		HorizontalPanel passwordField = new HorizontalPanel();
		Label passwordLabel = new Label("Password");
		passwordLabel.setWidth("150px");
		passwordField.add(passwordLabel);
		passwordEntry = new PasswordTextBox();
		passwordEntry.setWidth("250px");
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
		forgotPasswordButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				new UserForgotPassword(verticalPanel,LoginScreen.this.spectrumBrowser, LoginScreen.this).draw();
			}
		});
		buttonGrid.setWidget(0, 2, forgotPasswordButton);

		Button changePasswordButton = new Button("Change Password");
		changePasswordButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				new UserChangePassword(verticalPanel,LoginScreen.this.spectrumBrowser, LoginScreen.this).draw();
			}
		});
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
		RootPanel rootPanel = RootPanel.get();
		VerticalPanel rootVerticalPanel = new VerticalPanel();
		rootPanel.add(rootVerticalPanel);
		rootVerticalPanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		rootVerticalPanel.setWidth(Window.getClientWidth() + "px");

		
		
		HorizontalPanel hpanel = new HorizontalPanel();
		int height = 50;
		hpanel.setWidth(SpectrumBrowser.MAP_WIDTH  + "px");
		Image nistLogo = new Image( SpectrumBrowser.getIconsPath() + "nist-logo.png");
		nistLogo.setPixelSize((int)(215.0/95.0*height), height);
		Image ntiaLogo = new Image(SpectrumBrowser.getIconsPath() +  "ntia-logo.png");
		ntiaLogo.setPixelSize(height, height);
		hpanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
		hpanel.add(nistLogo);
		HTML html = new HTML("<h2>CAC Measured Spectrum Occupancy Database </h2>");
		hpanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		hpanel.add(html);
		hpanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_RIGHT);
		hpanel.add(ntiaLogo);
		
		rootVerticalPanel.add(verticalPanel);
		this.spectrumBrowser = spectrumBrowser;
	}

}
