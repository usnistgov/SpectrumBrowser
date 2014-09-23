package gov.nist.spectrumbrowser.client;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.Scheduler;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

public class DowloadData implements SpectrumBrowserCallback<String> {

	private SpectrumBrowser spectrumBrowser;
	private SpectrumBrowserShowDatasets spectrumBrowserShowDataSets;
	private VerticalPanel verticalPanel;
	private int dayCount;
	private long tSelectedStartTime;
	private String sensorId;
	private MenuBar menuBar;
	private long subBandMinFreq;
	private long subBandMaxFreq;
	private Button checkButton;
	private HorizontalPanel urlPanel;
	private HTML title;
	private HorizontalPanel hpanel;

	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	public DowloadData(String sensorId, long tSelectedStartTime, int dayCount,
			long minFreq, long maxFreq, VerticalPanel verticalPanel,
			SpectrumBrowser spectrumBrowser,
			SpectrumBrowserShowDatasets spectrumBrowserShowDatasets) {
		this.spectrumBrowser = spectrumBrowser;
		this.spectrumBrowserShowDataSets = spectrumBrowserShowDatasets;
		this.verticalPanel = verticalPanel;
		this.dayCount = dayCount;
		this.tSelectedStartTime = tSelectedStartTime;
		this.sensorId = sensorId;
		spectrumBrowser.getSpectrumBrowserService().generateZipFileForDownload(
				spectrumBrowser.getSessionId(), sensorId, tSelectedStartTime,
				dayCount, minFreq, maxFreq, this);
	}

	public void draw() {
		verticalPanel.clear();
		verticalPanel.setTitle("");
		menuBar = new MenuBar();
		menuBar.addItem(
				new SafeHtmlBuilder().appendEscaped(
						SpectrumBrowser.LOGOFF_LABEL).toSafeHtml(),
				new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {
						spectrumBrowser.logoff();
					}
				});

		menuBar.addItem(
				new SafeHtmlBuilder().appendEscaped(
						SpectrumBrowserShowDatasets.END_LABEL).toSafeHtml(),
				new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {
						spectrumBrowserShowDataSets.buildUi();
					}
				});
		verticalPanel.add(menuBar);

	}

	class CheckForDataAvailability implements ClickHandler,
			SpectrumBrowserCallback<String> {

		String uri;
		String url;

		CheckForDataAvailability(String uri, String url) {
			this.uri = uri;
			this.url = url;
		}

		@Override
		public void onClick(ClickEvent event) {
			spectrumBrowser.getSpectrumBrowserService()
					.checkForDumpAvailability(spectrumBrowser.getSessionId(),
							uri, this);

		}

		@Override
		public void onSuccess(String result) {
			JSONValue jsonValue = JSONParser.parseLenient(result);
			String status = jsonValue.isObject().get("status").isString()
					.stringValue();
			if (status.equals("OK")) {
				title.setText("Click on URL below to retrieve your data");
				checkButton.setVisible(false);
				checkButton.setEnabled(false);
				hpanel.setVisible(false);
				urlPanel.clear();
				HTML html = new HTML("<a href=\"" + url + "\">" + url + "</a>");
				urlPanel.add(html);
			} else {
				urlPanel.clear();
				HTML html = new HTML(
						"<h4> Dump not yet ready. Try again in 5 minutes. </h4>");
				urlPanel.add(html);
			}
		}

		@Override
		public void onFailure(Throwable throwable) {
			logger.log(Level.SEVERE, "Error contacting server", throwable);
			spectrumBrowser.displayError("Error Contacting Server");
		}

	}

	@Override
	public void onSuccess(String result) {
		try {
			JSONValue jsonValue = JSONParser.parseLenient(result);
			JSONObject jsonObject = jsonValue.isObject();
			final String uri = jsonObject.get("dump").isString().stringValue();
			String url = SpectrumBrowser.getGeneratedDataPath() + uri;
			logger.finer("URL for data " + url);
			checkButton = new Button("Click to check for data availability");
			checkButton.addClickHandler(new CheckForDataAvailability(uri, url));
			title = new HTML("<h2>Bundling requested data</h2>");
			verticalPanel.add(title);
			verticalPanel.add(checkButton);

			urlPanel = new HorizontalPanel();
			verticalPanel.add(urlPanel);

			hpanel = new HorizontalPanel();
			Label label1 = new Label("Email notification:");
			label1.setTitle("Enter your email address and submit for email notification");
			hpanel.add(label1);
			final TextBox textBox = new TextBox();
			textBox.setWidth("200px");
			hpanel.add(textBox);
			Button submitButton = new Button();
			submitButton.setStyleName("sendButton");
			submitButton.setText("Submit");
			hpanel.add(submitButton);
			submitButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					String emailAddress = textBox.getValue();
					if (!emailAddress
							.matches("^[_A-Za-z0-9-]+(\\.[_A-Za-z0-9-]+)*@[A-Za-z0-9]+(\\.[A-Za-z0-9]+)*(\\.[A-Za-z]{2,})$")) {
						Window.alert("Please enter a valid email address.");
						return;
					}
					spectrumBrowser.getSpectrumBrowserService().emailUrlToUser(
							spectrumBrowser.getSessionId(),
							spectrumBrowser.getBaseUrl(), uri,
							textBox.getValue(),
							new SpectrumBrowserCallback<String>() {

								@Override
								public void onSuccess(String result) {
									Window.alert("Check your email for notification");

								}

								@Override
								public void onFailure(Throwable throwable) {
									Window.alert("Error communicating with server");

								}
							});

				}
			});
			verticalPanel.add(hpanel);

		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Error parsing json file ", th);
		}

	}

	@Override
	public void onFailure(Throwable throwable) {
		Window.alert("Error contacting web service");
	}

}
