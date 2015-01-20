package gov.nist.spectrumbrowser.admin;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowser;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.EntryPoint;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.PasswordTextBox;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

/**
 * Sample admin screen.
 * 
 * @author mranga
 * 
 *         Note: this is a sample admin screen class. It is structured in the
 *         same way as the other screens (i.e. it implements
 *         SpectrumBrowserCallback). Right now it does nothing useful.
 */
class Admin extends AbstractSpectrumBrowser implements EntryPoint,
		SpectrumBrowserScreen {

	private VerticalPanel verticalPanel;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	PasswordTextBox passwordEntry;
	TextBox nameEntry;
	String locationName;
	private boolean isUserLoggedIn;


	private static final String HEADING_TEXT = "CAC Measured Spectrum Occupancy Database Administrator Interface";
	private static final String WELCOME_TEXT = "Non administrators, vamoose!";

	public static final String LOGOFF_LABEL = "Logoff";
	private static final String END_LABEL = "Admin";

	private static AdminService adminService = new AdminServiceImpl(
			getBaseUrl());
	
	private class SendNamePasswordToServer implements ClickHandler {

		@Override
		public void onClick(ClickEvent clickEvent) {
			try {
				logger.finer("onClick");
				String name = nameEntry.getText();
				String password = passwordEntry.getText();
				logger.finer("SendNamePasswordToServer: " + name);
				if (name == null || name.length() == 0) {
					Window.alert("Name is mandatory");
					return;
				}

				adminService.authenticate(name, password, "admin",
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
								try {
									JSONValue jsonValue = JSONParser
											.parseStrict(result);
									JSONObject jsonObject = jsonValue
											.isObject();
									String res = jsonObject.get("status")
											.isString().stringValue();
									if (res.startsWith("OK")) {
										setSessionToken(jsonObject
												.get("sessionId").isString()
												.stringValue());
										isUserLoggedIn = true;
										new AdminScreen(verticalPanel,
												Admin.this).draw();
									} else {
										Window.alert("Username or Password is incorrect. Please try again");
									}
								} catch (Throwable ex) {
									Window.alert("Problem parsing json");
									logger.log(Level.SEVERE, " Problem parsing json",ex);
									
								}
							}
						});

			} catch (Throwable th) {
				logger.log(Level.SEVERE, "Problem contacting server ", th);
				Window.alert("Problem contacting server");
			}
		}

	}

	public void draw() {
		RootPanel.get().clear();
		verticalPanel = new VerticalPanel();
		HTML heading =  new HTML("<h1>" + HEADING_TEXT +  "</h1>");
		verticalPanel.add(heading);
		verticalPanel
				.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		verticalPanel.setStyleName("loginPanel");
		verticalPanel.setSpacing(20);
		RootPanel.get().add(verticalPanel);
		HorizontalPanel nameField = new HorizontalPanel();
		// Should use internationalization. for now just hard code it.
		Label nameLabel = new Label("Admin Email Address");
		nameLabel.setWidth("150px");
		nameField.add(nameLabel);
		nameEntry = new TextBox();
		nameEntry.setText("admin@nist.gov");
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

		Button sendButton = new Button("Log in");
		// We can add style names to widgets
		// sendButton.addStyleName("sendButton");
		HorizontalPanel horizontalPanel = new HorizontalPanel();
		horizontalPanel.add(sendButton);
		verticalPanel.add(horizontalPanel);
		sendButton.addClickHandler(new SendNamePasswordToServer());


	}

	

	@Override
	public void onModuleLoad() {
		draw();

	}

	public void logoff() {
		adminService.logOut(
				new SpectrumBrowserCallback<String>() {

					@Override
					public void onSuccess(String result) {
						RootPanel.get().clear();
						onModuleLoad();
					}

					@Override
					public void onFailure(Throwable throwable) {
						Window.alert("Error communicating with server");
						onModuleLoad();
					}

				});
	}

	public static AdminService getAdminService() {
		return adminService;
	}

	@Override
	public String getLabel() {
		return END_LABEL + " >>";
	}

	@Override
	public String getEndLabel() {
		return END_LABEL;
	}
	
	@Override
	public boolean isUserLoggedIn() {
		return this.isUserLoggedIn;
	}

}
