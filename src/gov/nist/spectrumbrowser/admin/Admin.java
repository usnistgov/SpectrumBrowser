package gov.nist.spectrumbrowser.admin;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowser;
import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.EntryPoint;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.dom.client.KeyCodes;
import com.google.gwt.event.dom.client.KeyDownEvent;
import com.google.gwt.event.dom.client.KeyDownHandler;
import com.google.gwt.event.logical.shared.CloseEvent;
import com.google.gwt.event.logical.shared.CloseHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Cookies;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.Window.ClosingEvent;
import com.google.gwt.user.client.Window.ClosingHandler;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.PasswordTextBox;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

/**
 * Admin screen.
 */
public class Admin extends AbstractSpectrumBrowser implements EntryPoint, SpectrumBrowserScreen {
	private Button sendButton;
	private boolean isUserLoggedIn;
	private static TextBox emailEntry;
	private VerticalPanel verticalPanel;
	private MyHandler handler = new MyHandler();
	private static PasswordTextBox passwordEntry;
	private static final String END_LABEL = "Admin";
	public static final String LOGOFF_LABEL = "Logoff";
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private static AdminService adminService = new AdminServiceImpl(getBaseUrl());
	private static final String HEADING_TEXT = "CAC Measured Spectrum Occupancy Database Administrator Interface";
	private AdminScreen adminScreen;
	private static String COOKIE = "gov.nist.spectrumbrowser.admin.token";
	static {
		Window.addWindowClosingHandler(new ClosingHandler() {
			@Override
			public void onWindowClosing(ClosingEvent event) {
				event.setMessage("Spectrum Browser: Close this window?");
			}
		});
		Window.addCloseHandler(new CloseHandler<Window>() {
			@Override
			public void onClose(CloseEvent<Window> event) {
				adminService.logOut(new SpectrumBrowserCallback<String>() {
					@Override
					public void onSuccess(String result) {
						Window.alert("Successfully logged off.");
					}

					@Override
					public void onFailure(Throwable throwable) {
						// TODO Auto-generated method stub

					}
				});
			}
		});
	}
	
	@Override
	public void onModuleLoad() {
		String sessionToken = Cookies.getCookie(COOKIE);
		if (sessionToken != null) {
			Admin.setSessionToken(sessionToken);
			Admin.getAdminService().verifySessionToken( new SpectrumBrowserCallback<String>() {

				@Override
				public void onSuccess(String result) {
					JSONObject jsonObject = JSONParser.parseLenient(result).isObject();
					if (jsonObject.get("status").isString().stringValue().equals("OK")) {
						RootPanel.get().clear();
				
						Window.setTitle("MSOD:Admin");
						verticalPanel = new VerticalPanel();
						verticalPanel.setStyleName("loginPanel");
						verticalPanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
						verticalPanel.setSpacing(20);
						RootPanel.get().add(verticalPanel);
						isUserLoggedIn = true;
						adminScreen = new AdminScreen(verticalPanel, Admin.this);
						adminScreen.draw();
					} else {
						Cookies.removeCookie("gov.nist.spectrumbrowser.admin.token");
						draw();
					}
					
				}

				@Override
				public void onFailure(Throwable throwable) {
					 Window.alert("Error contacting server");
					 draw();
				}});
		} else {
			draw();
		}
	}

	public void draw() {
		RootPanel.get().clear();
		Window.setTitle("MSOD:Admin");
		verticalPanel = new VerticalPanel();
		HTML heading = new HTML("<h2>" + HEADING_TEXT + "</h2>");
		verticalPanel.add(heading);
		verticalPanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		verticalPanel.setStyleName("loginPanel");
		verticalPanel.setSpacing(20);
		RootPanel.get().add(verticalPanel);

		Grid grid = new Grid(2, 2);
		
		grid.setText(0, 0, "Email Address");
		emailEntry = new TextBox();
		emailEntry.setWidth("250px");
		emailEntry.addKeyDownHandler(handler);
		grid.setWidget(0, 1, emailEntry);
		
		grid.setText(1, 0, "Password");
		passwordEntry = new PasswordTextBox();
		passwordEntry.setWidth("250px");
		passwordEntry.addKeyDownHandler(handler);
		grid.setWidget(1, 1, passwordEntry);
		
		grid.getCellFormatter().addStyleName(0, 0, "alignMagic");
		grid.getCellFormatter().addStyleName(1, 0, "alignMagic");
		
		verticalPanel.add(grid);

		sendButton = new Button("Log in");
		sendButton.addStyleName("sendButton");
		sendButton.addClickHandler(handler);
		
		HorizontalPanel horizontalPanel = new HorizontalPanel();
		horizontalPanel.add(sendButton);
		verticalPanel.add(horizontalPanel);

	}
	
	private void loginHandler() {
		String emailAddress, password;
		emailAddress = password = "";
		
		emailAddress = emailEntry.getValue().trim();
		password = passwordEntry.getValue();			

		logger.finer("LogintoServer: " + emailAddress);
		if (emailAddress == null || emailAddress.length() == 0) {
			Window.alert("Email address is required");
			return;
		}
		if (password == null || password.length() == 0) {
			Window.alert("Password is required");
			return;
		}
		JSONObject jsonObject  = new JSONObject();
		jsonObject.put(Defines.ACCOUNT_EMAIL_ADDRESS, new JSONString(emailAddress));
		jsonObject.put(Defines.ACCOUNT_PASSWORD, new JSONString(password));
		jsonObject.put(Defines.ACCOUNT_PRIVILEGE, new JSONString(Defines.ADMIN_PRIVILEGE));

		adminService.authenticate(jsonObject.toString(), new SpectrumBrowserCallback<String>() {

			@Override
			public void onFailure(Throwable errorTrace) {
				logger.log(Level.SEVERE, "Error sending request to the server", errorTrace);
				if (! isUserLoggedIn) {
					Window.alert("Error communicating with the server.");
				}
			}

			@Override
			public void onSuccess(String result) {
				try {
					JSONValue jsonValue = JSONParser.parseStrict(result);
					JSONObject jsonObject = jsonValue.isObject();
					String status = jsonObject.get(Defines.STATUS).isString().stringValue();
					String statusMessage = jsonObject.get(Defines.STATUS_MESSAGE).isString().stringValue();
					if (status.equals("OK")) {
						String sessionToken = jsonObject.get(Defines.SESSION_ID).isString().stringValue();
						setSessionToken(sessionToken);
						Cookies.setCookie(COOKIE, sessionToken);
						isUserLoggedIn = true;
						adminScreen = new AdminScreen(verticalPanel, Admin.this);
						adminScreen.draw();
					} else {
						Window.alert(statusMessage);
					}
				} catch (Throwable ex) {
					Window.alert("Admin: Problem initializing application");
					logger.log(Level.SEVERE, " initializing application", ex);
					logoff();
 
				}
			}
		});
	}
	
	private class MyHandler implements ClickHandler, KeyDownHandler {

		@Override
		public void onKeyDown(KeyDownEvent event) {
			if (event.getNativeKeyCode() == KeyCodes.KEY_ENTER) {
				loginHandler();
			}
		}

		@Override
		public void onClick(ClickEvent event) {

			if (sendButton == event.getSource()) {
				loginHandler();
			}
		}

	}

	public void logoff() {
		if (! isUserLoggedIn) {
			return;
		}
		if (adminScreen != null) {
			adminScreen.cancelTimers();
		}
		Cookies.removeCookie(COOKIE);
		isUserLoggedIn = false;
		if (Admin.getSessionToken() == null) {
			RootPanel.get().clear();
			onModuleLoad();
		} else {
			adminService.logOut(new SpectrumBrowserCallback<String>() {
				@Override
				public void onSuccess(String result) {
					RootPanel.get().clear();
					Admin.destroySessionToken();
					onModuleLoad();
				}

				@Override
				public void onFailure(Throwable throwable) {
					onModuleLoad();
					Window.alert("Error Logging Off from server");
					Admin.destroySessionToken();
				}

			});
		}
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
