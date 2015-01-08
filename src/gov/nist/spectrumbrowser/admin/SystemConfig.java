package gov.nist.spectrumbrowser.admin;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.JavaScriptObject;
import com.google.gwt.core.client.JsonUtils;
import com.google.gwt.dom.client.Text;
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
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserWidget;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

public class SystemConfig extends AbstractSpectrumBrowserWidget implements
		SpectrumBrowserCallback<String>, SpectrumBrowserScreen {

	public static String END_LABEL = "System Config";
	private Grid grid;
	private TextBox apiKeyTextBox;
	private TextBox smtpServerTextBox;
	private TextBox smtpPortTextBox;
	private TextBox adminEmailAddressTextBox;
	private TextBox adminPasswordTextBox;
	private TextBox isAuthenticationRequiredTextBox;
	private TextBox myServerIdTextBox;
	private TextBox myServerKeyTextBox;
	private TextBox streamingCaptureSampleSizeTextBox;
	private TextBox streamingFilterTextBox;
	private TextBox streamingSamplingIntervalSecondsTextBox;
	private TextBox streamingSecondsPerFrame;
	private TextBox streamingServerPort;
	private JSONValue jsonValue;
	private JSONObject jsonObject;
	private Button logoutButton;
	private Button applyButton;
	private Button cancelButton;
	private Admin admin;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private boolean enablePasswordChecking = false;
	private boolean redraw = false;
	private TextBox myHostNameTextBox;

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
		grid = new Grid(15, 2);
		grid.setCellSpacing(2);
		grid.setCellSpacing(2);
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
		adminEmailAddressTextBox = new TextBox();
		adminEmailAddressTextBox
				.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						String email = event.getValue();
						if (email
								.matches("^[_A-Za-z0-9-]+(\\.[_A-Za-z0-9-]+)*@[A-Za-z0-9]+(\\.[A-Za-z0-9]+)*(\\.[A-Za-z]{2,})$")) {
							jsonObject.put("ADMIN_EMAIL_ADDRESS",
									new JSONString(email));
						} else {
							Window.alert("Please enter a valid email address");
							draw();
						}

					}
				});
		setText(counter++, "ADMIN_EMAIL_ADDRESS", "email-address of administrator",adminEmailAddressTextBox);
		
		adminPasswordTextBox = new TextBox();
		adminPasswordTextBox
				.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						String password = event.getValue();
						if (enablePasswordChecking
								&& !password
										.matches("((?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&+=])).{12,}$")) {
							Window.alert("Please enter a password with 1) at least 12 characters, "
									+ "2) a digit, 3) an upper case letter, "
									+ "4) a lower case letter, and "
									+ "5) a special character(!@#$%^&+=).");
						} else {
							jsonObject.put("ADMIN_PASSWORD", new JSONString(
									password));
						}
					}
				});
		setText(counter++, "ADMIN_PASSWORD", "Admin Password", adminPasswordTextBox);
		
		
		isAuthenticationRequiredTextBox = new TextBox();
		isAuthenticationRequiredTextBox
				.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						String flagString = event.getValue();
						try {
							boolean flag = Boolean.parseBoolean(flagString);
							jsonObject.put("IS_AUTHENTICATION_REQUIRED",
									JSONBoolean.getInstance(flag));
						} catch (Exception ex) {
							Window.alert("Enter true or false");
							draw();
						}
					}
				});
		setBoolean(counter++, "IS_AUTHENTICATION_REQUIRED", "User Authentication Required (true/false)?",
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
		setText(counter++, "API_KEY", "Google TimeZone API key", apiKeyTextBox);

		this.streamingFilterTextBox = new TextBox();
		streamingFilterTextBox
				.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						String filter = event.getValue();
						if (filter.equals("PEAK") || filter.equals("MEAN")) {
							jsonObject.put("STREAMING_FILTER", new JSONString(
									filter));
						} else {
							Window.alert("Filter must be PEAK or MEAN");
							draw();
						}

					}
				});
		setText(counter++, "STREAMING_FILTER", "Streaming filter (PEAK or MEAN)",streamingFilterTextBox);

		this.streamingCaptureSampleSizeTextBox = new TextBox();
		this.streamingCaptureSampleSizeTextBox
				.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						String sampleSizeStr = event.getValue();
						try {
							int sampleSize = Integer.parseInt(sampleSizeStr);
							if (sampleSize < 0) {
								Window.alert("Please enter integer > 0");
								draw();
								return;
							}
							jsonObject.put("STREAMING_CAPTURE_SAMPLE_SIZE_SECONDS",
									new JSONNumber(sampleSize));
						} catch (Exception ex) {
							Window.alert("Please enter an integer > 0");
							draw();
						}
					}
				});
		setInteger(counter++,"STREAMING_CAPTURE_SAMPLE_SIZE_SECONDS", "Seconds Per Captured Spectrogram",streamingCaptureSampleSizeTextBox);
		
		
		this.streamingSamplingIntervalSecondsTextBox = new TextBox();
		this.streamingSamplingIntervalSecondsTextBox.addValueChangeHandler( new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String sampleSizeStr = event.getValue();
				try {
					int sampleInterval = Integer.parseInt(sampleSizeStr);
					if (sampleInterval < 0) {
						Window.alert("Please enter integer > 0");
						draw();
						return;
					}
					jsonObject.put("STREAMING_SAMPLING_INTERVAL_SECONDS",
							new JSONNumber(sampleInterval));
				} catch (Exception ex) {
					Window.alert("Please enter an integer > 0");
					draw();
				}
			}});
		setInteger(counter++,"STREAMING_SAMPLING_INTERVAL_SECONDS","Seconds Between Captures From Stream",streamingSamplingIntervalSecondsTextBox);
		
		this.streamingSecondsPerFrame = new TextBox();
		this.streamingSecondsPerFrame.addValueChangeHandler(new ValueChangeHandler<String> () {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				String sampleSecondsPerFrameStr = event.getValue();
				try {
					float sampleSecondsPerFrame = Float.parseFloat(sampleSecondsPerFrameStr);
				
					if ( sampleSecondsPerFrame < 0.001 || sampleSecondsPerFrame > .1  ) {
						Window.alert("Range shoudl be from .001 to .1");
						draw();
						return;
					} else {
						jsonObject.put("STREAMING_SECONDS_PER_FRAME", new JSONNumber(sampleSecondsPerFrame));
					}
				} catch (Exception ex) {
					Window.alert("Please enter a number from .001 to .1");
					draw();
				}
			}
			
		});
		setFloat(counter++, "STREAMING_SECONDS_PER_FRAME","Streaming Time Resolution", streamingSecondsPerFrame);
		
		
		this.streamingServerPort = new TextBox();
		this.streamingServerPort.addValueChangeHandler(new ValueChangeHandler<String>() {

			@Override
			public void onValueChange(ValueChangeEvent<String> event) {
				// TODO Auto-generated method stub
				String streamingServerPortStr = event.getValue();
				try {
					int streamingServerPort = Integer.parseInt(streamingServerPortStr);
					if (streamingServerPort < 0) {
						Window.alert("Please enter integer > 0");
						draw();
						return;
					}
					jsonObject.put("STREAMING_SERVER_PORT",
							new JSONNumber(streamingServerPort));
				} catch (Exception ex) {
					Window.alert("Please enter an integer > 0");
					draw();
				}
			}});
		
		setInteger(counter++,"STREAMING_SERVER_PORT","Server port for inbound Streaming connections",streamingServerPort);
		

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
								if (jsonObj.get("Status").equals("OK")) {
									Window.alert("Configuration successfully updated");
								} else {
									Window.alert("Error in updating config - please re-enter");
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
