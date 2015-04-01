package gov.nist.spectrumbrowser.admin;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowser;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.EntryPoint;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.CloseEvent;
import com.google.gwt.event.logical.shared.CloseHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.Window.ClosingEvent;
import com.google.gwt.user.client.Window.ClosingHandler;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.PasswordTextBox;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

/**
 * Admin screen.
 */
class Admin extends AbstractSpectrumBrowser implements EntryPoint,
		SpectrumBrowserScreen {

	private VerticalPanel verticalPanel;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	PasswordTextBox passwordEntry;
	TextBox emailEntry;
	private boolean isUserLoggedIn;


	private static final String HEADING_TEXT = "CAC Measured Spectrum Occupancy Database Administrator Interface";

	public static final String LOGOFF_LABEL = "Logoff";
	private static final String END_LABEL = "Admin";

	private static AdminService adminService = new AdminServiceImpl(
			getBaseUrl());
	
	static {
		 Window.addWindowClosingHandler(new ClosingHandler() {

				@Override
				public void onWindowClosing(ClosingEvent event) {
					
					event.setMessage("Spectrum Browser: Close this window?");

				}
			});
		 Window.addCloseHandler(new CloseHandler<Window> (){

			@Override
			public void onClose(CloseEvent<Window> event) {
				adminService.logOut(new SpectrumBrowserCallback<String> () {

					@Override
					public void onSuccess(String result) {
						Window.alert("Successfully logged off.");
					}

					@Override
					public void onFailure(Throwable throwable) {
						// TODO Auto-generated method stub
						
					}});
			}});
	}
	
	private class SendNamePasswordToServer implements ClickHandler {

		@Override
		public void onClick(ClickEvent clickEvent) {
			try {
				logger.finer("onClick");
				
				String password = "";
				String emailAddress = "";
				try {
					password = passwordEntry.getValue();
					emailAddress = emailEntry.getValue().trim();					
				}
				catch (Throwable th) {
					//not a problem, since we will check for null's below.
				}
				if (emailAddress == null || emailAddress.length() == 0) {
					Window.alert("Email address is required.");
					return;
				}
				if (password == null || password.length() == 0) {
					Window.alert("Password is required.");
					return;
				}
				JSONObject jsonObject  = new JSONObject();
				jsonObject.put(AbstractSpectrumBrowser.ACCOUNT_EMAIL_ADDRESS, new JSONString(emailAddress));
				jsonObject.put(AbstractSpectrumBrowser.ACCOUNT_PASSWORD, new JSONString(password));
				jsonObject.put(AbstractSpectrumBrowser.ACCOUNT_PRIVILEGE, new JSONString(AbstractSpectrumBrowser.ADMIN_PRIVILEGE));

				adminService.authenticate(jsonObject.toString(),
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
									String res = jsonObject.get(AbstractSpectrumBrowser.STATUS)
											.isString().stringValue();
									if (res.equals("OK")) {
										setSessionToken(jsonObject.get("sessionId").isString().stringValue());
										isUserLoggedIn = true;
										new AdminScreen(verticalPanel,
												Admin.this).draw();
									} 
									else {
										String statusMessage = jsonObject.get(AbstractSpectrumBrowser.STATUS_MESSAGE).isString().stringValue();
										Window.alert(statusMessage);
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
		
		Grid grid = new Grid(2,2);
		grid.setText(0, 0, "Email Address");
		emailEntry = new TextBox();
		emailEntry.setWidth("250px");
		emailEntry.setFocus(true);
		grid.setWidget(0, 1, emailEntry);
		grid.setText(1,0, "Password");
		passwordEntry = new PasswordTextBox();
		grid.setWidget(1, 1, passwordEntry);
		verticalPanel.add(grid);

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
