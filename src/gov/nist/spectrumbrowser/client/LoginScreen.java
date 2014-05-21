package gov.nist.spectrumbrowser.client;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.dom.client.Document;
import com.google.gwt.dom.client.HeadingElement;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.PasswordTextBox;
import com.google.gwt.user.client.ui.PopupPanel;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
public class LoginScreen {
	VerticalPanel verticalPanel;
	static Logger logger = Logger.getLogger("SpectrumBrowser");
	PasswordTextBox passwordEntry;
	TextBox nameEntry;
	String locationName;
	PopupPanel popupPanel = new PopupPanel();
	String sessionToken;
	HeadingElement helement;
	HeadingElement welcomeElement;
	boolean adminUser;

	/**
	 * Create a remote service proxy to talk to the server-side Greeting
	 * service.
	 */
	private SpectrumBrowser spectrumBrowser;

	

	/**
	 * The message displayed to the user when the server cannot be reached or
	 * returns an error.
	 */
	private static final String SERVER_ERROR = "An error occurred while "
			+ "attempting to contact the server. Please check your network "
			+ "connection and try again.";
	private static final String HEADING_TEXT = 
			"Department of Commerce Spectrum Monitoring Project.";

	/**
	 * The welcome text. This should be defined as a resource in another file
	 * For now we hard code it here.
	 */
	private static final String WELCOME_TEXT = 
			"Welcome to the Department of Commerce Spectrum Monitoring Project.\n"
			+ "The goal of this project is to monitor the 3.5 Ghz spectrum and \n"
			+ "to allow the user to examine spectrum utilization at various locations. \n"
			+ "Enter User Name and password or enter guest with null password for guest access";
	

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
			
			getSpectrumBrowserService().authenticate(
					name,password, adminUser? "admin": "user",
					new SpectrumBrowserCallback<String>() {

						@Override
						public void onFailure(Throwable errorTrace) {
							logger.log(Level.SEVERE,
									"Error sending request to the server",errorTrace);
							Window.alert("Error communicating with the server.");
						
						
						}

						@Override
						public void onSuccess(String result) {
							JSONValue jsonValue = JSONParser.parseStrict(result);
							JSONObject jsonObject = jsonValue.isObject();
							String res = jsonObject.get("status").isString().stringValue();
							if (res.startsWith("OK")) {
								sessionToken = jsonObject.get("sessionId").isString().stringValue();
								spectrumBrowser.setSessionToken(sessionToken);
								verticalPanel.clear();
								helement.removeFromParent();
								welcomeElement.removeFromParent();
								new SpectrumBrowserShowDatasets(spectrumBrowser, verticalPanel);
							} else {
								Window.alert("Username or Password is incorrect. Please try again");
							}
						}
					});

		}

	}
	
	/**
	 * Display the error message and put up the login screen again.
	 * @param errorMessage
	 */
	public void displayError(String errorMessage) {
		Window.alert(errorMessage);
		logoff();
		
	}
	
	SpectrumBrowserServiceAsync getSpectrumBrowserService() {
		return spectrumBrowser.getSpectrumBrowserService();
	}

	/**
	 * This is the entry point method.
	 */
	public void draw() {

		
		logger.log(Level.INFO, "Base URL " + spectrumBrowser.getBaseUrl());
		helement = Document.get().createHElement(1);
		helement.setInnerText(HEADING_TEXT);
	    RootPanel.get().getElement().appendChild(helement);
	    welcomeElement = Document.get().createHElement(2);
	    welcomeElement.setInnerText(WELCOME_TEXT);
	    RootPanel.get().getElement().appendChild(welcomeElement);
		verticalPanel = new VerticalPanel();
		verticalPanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		verticalPanel.setStyleName("loginPanel");
		verticalPanel.setSpacing(20);
	    RootPanel.get().add(verticalPanel);
		HorizontalPanel nameField = new HorizontalPanel();
		// Should use internationalization. for now just hard code it.
		Label nameLabel = new Label("User Name");
		nameLabel.setWidth("150px");
		nameField.add(nameLabel);
		nameEntry = new TextBox();
		nameEntry.setText("guest");
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
		
		CheckBox cb = new CheckBox("Login as Admin");
		verticalPanel.add(cb);
		cb.addClickHandler( new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				adminUser = adminUser? false : true;
				
			}} );
		
		

		 Button sendButton = new Button("Log in");
		// We can add style names to widgets
		sendButton.addStyleName("sendButton");
		verticalPanel.add(sendButton);
			
		// Add the nameField and sendButton to the RootPanel
		// Use RootPanel.get() to get the entire body element

		// Focus the cursor on the name field when the app loads
		nameEntry.setFocus(true);
		nameEntry.selectAll();

		sendButton.addClickHandler(new SendNamePasswordToServer());
	}

	public void logoff() {
		
		getSpectrumBrowserService().logOut(sessionToken, new SpectrumBrowserCallback<String>() {

			@Override
			public void onFailure(Throwable caught) {
				RootPanel.get().clear();
				draw();
			}

			@Override
			public void onSuccess(String result) {
				// TODO Auto-generated method stub
				RootPanel.get().clear();
				draw();
			}} );
	}
	
	public LoginScreen(SpectrumBrowser spectrumBrowser) {
		this.spectrumBrowser = spectrumBrowser;
	}
	

}
