package gov.nist.spectrumbrowser.admin;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserWidget;
import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONBoolean;
import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.PasswordTextBox;
import com.google.gwt.user.client.ui.TextBox;

public class SystemConfig extends AbstractSpectrumBrowserWidget implements
		SpectrumBrowserCallback<String>, SpectrumBrowserScreen {

	public static String END_LABEL = "System Config";
	private Grid grid;
	private TextBox apiKeyTextBox;
	private TextBox smtpServerTextBox;
	private TextBox smtpPortTextBox;
	private TextBox smtpEmailAddressTextBox;
	private TextBox isAuthenticationRequiredTextBox;
	private TextBox myServerIdTextBox;
	private TextBox myServerKeyTextBox;
	private TextBox useLDAPTextBox;
	private TextBox accountNumFailedLoginAttemptsTextBox;
	private TextBox changePasswordIntervalDaysTextBox;
	private TextBox userAccountAcknowHoursTextBox;
	private TextBox accountRequestTimeoutHoursTextBox;
	private JSONValue jsonValue;
	private JSONObject jsonObject;
	private Button logoutButton;
	private Button applyButton;
	private Button cancelButton;
	private Admin admin;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private boolean redraw = false;
	private TextBox myHostNameTextBox;
	private TextBox myPortTextBox;
	private TextBox myRefreshIntervalTextBox;
	private TextBox myProtocolTextBox;
	private TextBox userSessionTimeoutMinutes;
	private TextBox adminSessionTimeoutMinutes;
	private TextBox sslCert;
	private TextBox minStreamingInterArrivalTimeSeconds;
	


	public SystemConfig(Admin admin) {
		super();
		try {
			this.admin = admin;
			Admin.getAdminService().getSystemConfig(this);
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Problem contacting server", th);
			Window.alert("Problem contacting server");
			admin.logoff();
		}

	}

	@Override
	public void onSuccess(String jsonString) {
		try {
			jsonValue = JSONParser.parseLenient(jsonString);
			jsonObject = jsonValue.isObject();
			if (redraw) {
				draw();
			}
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Error Parsing JSON message", th);
			admin.logoff();
		}

	}

	@Override
	public void onFailure(Throwable throwable) {
		logger.log(Level.SEVERE, "Error Communicating with server message",
				throwable);
		admin.logoff();
	}

	private void setText(int row, String key, String fieldName, TextBox widget) {
		grid.setText(row, 0,fieldName);
		String value = super.getAsString(jsonValue, key);
		widget.setText(value);
		grid.setWidget(row, 1, widget);
	}

	private void setInteger(int row, String key, String fieldName, TextBox widget) {
		grid.setText(row, 0, fieldName);
		int value = super.getAsInt(jsonValue, key);
		widget.setText(Integer.toString(value));
		grid.setWidget(row, 1, widget);
	}

	private void setLabel(int row, String key, TextBox widget) {
		grid.setText(row, 0, key);
		String value = super.getAsString(jsonValue, key);
		widget.setText(value);
		grid.setWidget(row, 1, widget);
	}

	private void setBoolean(int row, String key, String fieldName, TextBox widget) {
		grid.setText(row, 0, fieldName);
		String value = Boolean.toString(super.getAsBoolean(jsonValue, key));
		widget.setText(value);
		grid.setWidget(row, 1, widget);
	}
	
	private void setFloat(int row, String key, String fieldName, TextBox widget) {
		grid.setText(row, 0, fieldName);
		String value = Float.toString(super.getAsFloat(jsonValue,key));
		widget.setText(value);
		grid.setWidget(row, 1, widget);
	}

	@Override
	public void draw() {
		verticalPanel.clear();
		// HTML title = new HTML("<h3>System Configuration </h3>");
		// verticalPanel.add(title);
		grid = new Grid(20, 2);
		grid.setCellSpacing(4);
		grid.setBorderWidth(2);
		verticalPanel.add(grid);

		int counter = 0;
		myHostNameTextBox = new TextBox();
		myHostNameTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {
			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String hostName = event.getValue();
				jsonObject.put("HOST_NAME", new JSONString(hostName));
				
			}});
		setText(counter++,"HOST_NAME","Public Host Name ", myHostNameTextBox);
		
		myPortTextBox = new TextBox();
		myPortTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String publicPort = event.getValue();
				try {
					int publicPortInt = Integer.parseInt(publicPort);
					if (publicPortInt < 0 ) {
						Window.alert("Publicly accessible port for server HTTP(s) access");
						return;
					}
					jsonObject.put("PUBLIC_PORT", new JSONNumber(publicPortInt));
				} catch (NumberFormatException ex) {
					Window.alert("Specify publicly accessible port (int)");
				}
				
			}});
		setInteger(counter++,"PUBLIC_PORT","Public Web Server Port ", myPortTextBox);
		
		myProtocolTextBox = new TextBox();
		myProtocolTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String protocol = event.getValue();
				if (!protocol.equals("http") && !protocol.equals("https")) {
					Window.alert("please specify http or https");
				}
				jsonObject.put("PROTOCOL", new JSONString(protocol));
				
			}});
		setText(counter++,"PROTOCOL","Server access protocol",myProtocolTextBox);
		

		myServerIdTextBox = new TextBox();
		myServerIdTextBox
				.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						String serverId = event.getValue();
						jsonObject
								.put("MY_SERVER_ID", new JSONString(serverId));
					}
				});
		myServerIdTextBox.setTitle("Server ID must be unique across federation. Used to identify server to federation peers");
		setText(counter++, "MY_SERVER_ID", "Unique ID for this server", myServerIdTextBox);
			
		myServerKeyTextBox = new TextBox();
		myServerKeyTextBox
				.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						String serverKey = event.getValue();
						jsonObject.put("MY_SERVER_KEY", new JSONString(
								serverKey));
					}
				});
		myServerKeyTextBox.setTitle("Server key used to authenticate server to federation peers.");
		setText(counter++, "MY_SERVER_KEY", "Server Key", myServerKeyTextBox);
		
		smtpServerTextBox = new TextBox();
		smtpServerTextBox
				.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						String smtpServer = event.getValue();
						jsonObject.put("SMTP_SERVER",
								new JSONString(smtpServer));
					}
				});

		setText(counter++, "SMTP_SERVER", "Host Name for SMTP server", smtpServerTextBox);
		smtpPortTextBox = new TextBox();
		smtpPortTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				try {
					String portString = event.getValue();
					int port = Integer.parseInt(portString);
					jsonObject.put("SMTP_PORT", new JSONNumber(port));
				} catch (Exception exception) {
					Window.alert("Invalid port");
					draw();
				}
			}
		});
		setInteger(counter++, "SMTP_PORT", "Mail Server Port",smtpPortTextBox);
		
		
		smtpEmailAddressTextBox = new TextBox();
		smtpEmailAddressTextBox
				.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						String email = event.getValue();
						if (email
								.matches("^[_A-Za-z0-9-]+(\\.[_A-Za-z0-9-]+)*@[A-Za-z0-9-]+(\\.[A-Za-z0-9-]+)*(\\.[A-Za-z]{2,})$"))  {
							jsonObject.put("SMTP_EMAIL_ADDRESS",
									new JSONString(email));
						} else {
							Window.alert("Please enter a valid SMTP email address");
							draw();
						}

					}
				});
		setText(counter++, "SMTP_EMAIL_ADDRESS", "Email to use for mail FROM this server",smtpEmailAddressTextBox);
		
		
		isAuthenticationRequiredTextBox = new TextBox();
		isAuthenticationRequiredTextBox
				.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						String flagString = event.getValue();
						try {
							boolean flag = Boolean.parseBoolean(flagString);
							jsonObject.put(Defines.IS_AUTHENTICATION_REQUIRED,
									JSONBoolean.getInstance(flag));
						} catch (Exception ex) {
							Window.alert("Enter true or false");
							draw();
						}
					}
				});
		isAuthenticationRequiredTextBox.setTitle("Start page will display a login screen if true");
		setBoolean(counter++, Defines.IS_AUTHENTICATION_REQUIRED, "User Authentication Required (true/false)?",
				isAuthenticationRequiredTextBox);

		apiKeyTextBox = new TextBox();
		apiKeyTextBox.setTitle("Google Timezone API key");
		apiKeyTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String apiKey = event.getValue();
				jsonObject.put("API_KEY", new JSONString(apiKey));
			}
		});
		apiKeyTextBox.setText("Request google for an API key.");
		setText(counter++, "API_KEY", "Google TimeZone API key", apiKeyTextBox);

		this.minStreamingInterArrivalTimeSeconds = new TextBox();
		this.minStreamingInterArrivalTimeSeconds.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				// TODO Auto-generated method stub
				String minStreamingTimeStr = event.getValue();
				try {
					double minStreamingInterArrivalTimeSeconds = Double.parseDouble(minStreamingTimeStr);
					if (minStreamingInterArrivalTimeSeconds < 0) {
						Window.alert("Please enter value > 0");
						draw();
						return;
					}
					jsonObject.put(Defines.MIN_STREAMING_INTER_ARRIVAL_TIME_SECONDS,
							new JSONNumber(minStreamingInterArrivalTimeSeconds));
				} catch (Exception ex) {
					Window.alert("Please enter an integer > 0");
					draw();
				}
			}});		
		setFloat(counter++,Defines.MIN_STREAMING_INTER_ARRIVAL_TIME_SECONDS,"Min time (s) between successive spectra from streaming sensor",
				minStreamingInterArrivalTimeSeconds);
		
		
		myRefreshIntervalTextBox = new TextBox();
		myRefreshIntervalTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String refreshInterval = event.getValue();
				try {
					int refreshIntervalInt = Integer.parseInt(refreshInterval);
					if (refreshIntervalInt < 10 ) {
						Window.alert("Specify value above 10");
						return;
					}
					jsonObject.put("SOFT_STATE_REFRESH_INTERVAL", new JSONNumber(refreshIntervalInt));
				} catch (NumberFormatException ex) {
					Window.alert("Specify soft state refresh interval (seconds) for federation.");
				}
				
			}});
		setInteger(counter++,"SOFT_STATE_REFRESH_INTERVAL","Peering soft state refresh interval (s) ", myRefreshIntervalTextBox);

		useLDAPTextBox = new TextBox();
		useLDAPTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						String flagString = event.getValue();
						try {
							boolean flag = Boolean.parseBoolean(flagString);
							jsonObject.put("USE_LDAP",
									JSONBoolean.getInstance(flag));
						} catch (Exception ex) {
							Window.alert("Enter true or false");
							draw();
						}
					}
				});
		setBoolean(counter++, "USE_LDAP", "Use LDAP to store user accounts (true/false)?",
				useLDAPTextBox);
		
		accountNumFailedLoginAttemptsTextBox = new TextBox();
		accountNumFailedLoginAttemptsTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String accountNumFailedLoginAttempts = event.getValue();
				try {
					int accountNumFailedLoginAttemptsInt = Integer.parseInt(accountNumFailedLoginAttempts);
					if (accountNumFailedLoginAttemptsInt < 1 ) {
						Window.alert("Specify value above 0");
						return;
					}
					jsonObject.put("ACCOUNT_NUM_FAILED_LOGIN_ATTEMPTS", new JSONNumber(accountNumFailedLoginAttemptsInt));
				} catch (NumberFormatException ex) {
					Window.alert("Specify number of login attempts (e.g. 3) before the user is locked out.");
				}
				
			}});
		setInteger(counter++,"ACCOUNT_NUM_FAILED_LOGIN_ATTEMPTS","Number of failed login attempts before user is locked out ", accountNumFailedLoginAttemptsTextBox);
		
		changePasswordIntervalDaysTextBox = new TextBox();
		changePasswordIntervalDaysTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String changePasswordIntervalDays = event.getValue();
				try {
					int changePasswordIntervalDaysInt = Integer.parseInt(changePasswordIntervalDays);
					if (changePasswordIntervalDaysInt < 1 ) {
						Window.alert("Specify value above 0");
						return;
					}
					jsonObject.put("CHANGE_PASSWORD_INTERVAL_DAYS", new JSONNumber(changePasswordIntervalDaysInt));
				} catch (NumberFormatException ex) {
					Window.alert("Specify the interval (in days) for how often a user must change their password.");
				}
				
			}});
		setInteger(counter++,"CHANGE_PASSWORD_INTERVAL_DAYS","Interval (in days) between required password changes ", changePasswordIntervalDaysTextBox);

		userAccountAcknowHoursTextBox = new TextBox();
		userAccountAcknowHoursTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String userAccountAcknowHours = event.getValue();
				try {
					int userAccountAcknowHoursInt = Integer.parseInt(userAccountAcknowHours);
					if (userAccountAcknowHoursInt < 1 ) {
						Window.alert("Specify value above 0");
						return;
					}
					jsonObject.put("ACCOUNT_USER_ACKNOW_HOURS", new JSONNumber(userAccountAcknowHoursInt));
				} catch (NumberFormatException ex) {
					Window.alert("Specify the interval (in hours) for how the user gets to click in an email link for account authorization or password resets. ");
				}
				
			}});
		setInteger(counter++,"ACCOUNT_USER_ACKNOW_HOURS","Interval (in hours) for user to activate account or reset password ", userAccountAcknowHoursTextBox);

		accountRequestTimeoutHoursTextBox = new TextBox();
		accountRequestTimeoutHoursTextBox.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String accountRequestTimeoutHours = event.getValue();
				try {
					int accountRequestTimeoutHoursInt = Integer.parseInt(accountRequestTimeoutHours);
					if (accountRequestTimeoutHoursInt < 1 ) {
						Window.alert("Specify value above 1");
						return;
					}
					jsonObject.put("ACCOUNT_REQUEST_TIMEOUT_HOURS", new JSONNumber(accountRequestTimeoutHoursInt));
				} catch (NumberFormatException ex) {
					Window.alert("Specify the interval (in hours) for how the admin gets to click in an email link for account requests.");
				}
				
			}});
		setInteger(counter++,"ACCOUNT_REQUEST_TIMEOUT_HOURS","Interval (in hours) for admin to approve an account ", accountRequestTimeoutHoursTextBox);

		userSessionTimeoutMinutes = new TextBox();
		userSessionTimeoutMinutes.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String accountSessionTimeoutMinutesString = event.getValue();
				try {
					int userSessionTimeoutMinutes = Integer.parseInt(accountSessionTimeoutMinutesString);
					if ( userSessionTimeoutMinutes < 1) {
						Window.alert("Specify a value above 1");
						return;
					}
					jsonObject.put("USER_SESSION_TIMEOUT_MINUTES", new JSONNumber(userSessionTimeoutMinutes));
				} catch (NumberFormatException nfe) {
					Window.alert("Specify user session timeout in minutes.");
				}
			}});
		setInteger(counter++,"USER_SESSION_TIMEOUT_MINUTES","User session timeout (min)",userSessionTimeoutMinutes);
			
		adminSessionTimeoutMinutes = new TextBox();
		adminSessionTimeoutMinutes.addValueChangeHandler(new ValueChangeHandler<String>() {
			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String accountSessionTimeoutMinutesString = event.getValue();
				try {
					int adminSessionTimeoutMinutes = Integer.parseInt(accountSessionTimeoutMinutesString);
					if ( adminSessionTimeoutMinutes < 1) {
						Window.alert("Specify a value above 1");
						return;
					}
					jsonObject.put("ADMIN_SESSION_TIMEOUT_MINUTES", new JSONNumber(adminSessionTimeoutMinutes));
				} catch (NumberFormatException nfe) {
					Window.alert("Specify user session timeout in minutes.");
				}
			}});
		setInteger(counter++,"ADMIN_SESSION_TIMEOUT_MINUTES","Admin session timeout (min)",adminSessionTimeoutMinutes);
		
		sslCert = new TextBox();
		sslCert.addValueChangeHandler(new ValueChangeHandler<String> () {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String sslCert = event.getValue();
				if (sslCert == null || sslCert.equals("")) {
					Window.alert("Specify path to where certificate file is installed");
				}
				jsonObject.put("CERT", new JSONString(sslCert));
			}});
		setText(counter++,"CERT","path to certificate file",sslCert);
			
		
		
		for (int i = 0; i < grid.getRowCount(); i++) {
			grid.getCellFormatter().setStyleName(i, 0, "textLabelStyle");
		}

		applyButton = new Button("Apply Changes");
		cancelButton = new Button("Cancel Changes");
		logoutButton = new Button("Log Out");

		applyButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				Admin.getAdminService().setSystemConfig(jsonObject.toString(),
						new SpectrumBrowserCallback<String>() {

							@Override
							public void onSuccess(String result) {
								JSONObject jsonObj = JSONParser.parseLenient(result).isObject();
								if (jsonObj.get("status").isString().stringValue().equals("OK")) {
									Window.alert("Configuration successfully updated");
								} else {
									String errorMessage = jsonObj.get("ErrorMessage").isString().stringValue();
									Window.alert("Error in updating config - please re-enter. Error Message : "+errorMessage);
								}
							}

							@Override
							public void onFailure(Throwable throwable) {
								Window.alert("Error communicating with server");
								admin.logoff();
							}
						});
			}
		});

		cancelButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				redraw = true;
				Admin.getAdminService().getSystemConfig(SystemConfig.this);
			}
		});

		logoutButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}
		});

		HorizontalPanel buttonPanel = new HorizontalPanel();
		buttonPanel.add(applyButton);
		buttonPanel.add(cancelButton);
		buttonPanel.add(logoutButton);
		verticalPanel.add(buttonPanel);
	}

	@Override
	public String getLabel() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public String getEndLabel() {
		return END_LABEL;
	}

}
