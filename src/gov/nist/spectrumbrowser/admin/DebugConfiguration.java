package gov.nist.spectrumbrowser.admin;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.json.client.JSONBoolean;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserWidget;
import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

public class DebugConfiguration extends AbstractSpectrumBrowserWidget implements
		SpectrumBrowserScreen, SpectrumBrowserCallback<String> {
	private Admin admin;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private Grid grid;
	private JSONValue jsonValue;
	private JSONObject jsonObject;
	private boolean redraw;

	public DebugConfiguration(Admin admin) {
		this.admin = admin;
		Admin.getAdminService().getDebugFlags(this);
	}

	@Override
	public void onSuccess(String jsonString) {
		try {
			jsonValue = JSONParser.parseLenient(jsonString);
			String statusCode = jsonValue.isObject().get(Defines.STATUS)
					.isString().stringValue();
			if (statusCode.equals(Defines.OK)) {
				jsonObject = jsonValue.isObject().get("debugFlags").isObject();
				if (redraw) {
					draw();
				}
			} else {
				logger.log(Level.SEVERE, "Unexpected status code " + statusCode);
				Window.alert("Unexpected server response -- please inform admin");
				admin.logoff();
			}
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Error Parsing JSON message", th);
			admin.logoff();
		}
	}

	@Override
	public void onFailure(Throwable th) {
		logger.log(Level.SEVERE, "Error Contacting Server", th);
		admin.logoff();
	}

	@Override
	public void draw() {
		verticalPanel.clear();
		HTML title = new HTML("<h3>Debug flags</h3>");
		HTML helpText = new HTML(
				"<p>Note: Debug flags return to default values on server restart.</p>");

		verticalPanel.add(title);
		verticalPanel.add(helpText);
		grid = new Grid(jsonObject.keySet().size() + 1, 2);
		grid.setBorderWidth(2);
		grid.setCellPadding(2);
		grid.setCellPadding(2);
		grid.setText(0, 0, "Name");
		grid.setText(0, 1, "Value");
		int i = 1;
		for (final String key : jsonObject.keySet()) {

			grid.setWidget(i, 0, new Label(key));
			final CheckBox checkBox = new CheckBox();
			boolean value = jsonObject.get(key).isBoolean().booleanValue();
			checkBox.setValue(value);
			checkBox.addValueChangeHandler(new ValueChangeHandler<Boolean>() {
				@Override
				public void onValueChange(ValueChangeEvent<Boolean> event) {
					boolean value = event.getValue();
					jsonObject.put(key, JSONBoolean.getInstance(value));
					Admin.getAdminService().setDebugFlags(
							jsonObject.toString(),
							new SpectrumBrowserCallback<String>() {

								@Override
								public void onSuccess(String result) {
									try {
										JSONObject retval = JSONParser
												.parseLenient(result)
												.isObject();
										String status = retval.get("status")
												.isString().stringValue();
										if (!status.equals("OK")) {
											Window.alert("Unexpected response code");
											admin.logoff();
										}
									} catch (Throwable th) {
										Window.alert("error parsing response");
										logger.log(Level.SEVERE,
												"Error parsing response", th);
										admin.logoff();

									}
								}

								@Override
								public void onFailure(Throwable throwable) {
									Window.alert("error communicating with server");
									logger.log(Level.SEVERE,
											"Error communicating with server",
											throwable);
									admin.logoff();

								}
							});
				}
			});
			grid.setWidget(i, 1, checkBox);
			i++;
		}
		
		for (i = 0; i < grid.getColumnCount(); i++) {
			grid.getCellFormatter().setStyleName(0, i, "textLabelStyle");
		}
		
		for (i = 0; i < grid.getRowCount(); i++) {
			for (int j = 0; j < grid.getColumnCount(); j++) {
				grid.getCellFormatter().setHorizontalAlignment(i, j,
						HasHorizontalAlignment.ALIGN_CENTER);
				grid.getCellFormatter().setVerticalAlignment(i, j,
						HasVerticalAlignment.ALIGN_MIDDLE);
			}
		}
		verticalPanel.add(grid);
		
		final HorizontalPanel urlPanel = new HorizontalPanel();
		urlPanel.add( new Label("Click on logs button to fetch server logs"));
	
		Button getDebugLog = new Button("Logs");
		getDebugLog.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				Admin.getAdminService().getLogs(
						new SpectrumBrowserCallback<String>() {

							@Override
							public void onSuccess(String result) {
								try {
									JSONObject debugLogs = JSONParser
											.parseLenient(result).isObject();
									String url = debugLogs.get("url").isString().stringValue();
									urlPanel.clear();
									Label label = new Label( url);
									urlPanel.add(label);
								} catch (Throwable throwable) {
									logger.log(Level.SEVERE,
											"Error Parsing response ",
											throwable);
									admin.logoff();
								}
							}

							@Override
							public void onFailure(Throwable throwable) {
								logger.log(Level.SEVERE,
										"Error contacting server ", throwable);
								Window.alert("Error Parsing response");
								admin.logoff();
							}
						});
			}
		});
		
		verticalPanel.add(urlPanel);

		Button logoff = new Button("Log off");
		logoff.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();

			}
		});
		
		Button getTestCases = new Button("Get Test Cases");
		
		
		HorizontalPanel buttonPanel = new HorizontalPanel();
		buttonPanel.add(getDebugLog);
		buttonPanel.add(getTestCases);
		buttonPanel.add(logoff);
		verticalPanel.add(buttonPanel);

	}

	@Override
	public String getLabel() {
		return null;
	}

	@Override
	public String getEndLabel() {
		return "Debugging Logs";
	}

}
