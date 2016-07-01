/*
* Conditions Of Use 
* 
* This software was developed by employees of the National Institute of
* Standards and Technology (NIST), and others. 
* This software has been contributed to the public domain. 
* Pursuant to title 15 Untied States Code Section 105, works of NIST
* employees are not subject to copyright protection in the United States
* and are considered to be in the public domain. 
* As a result, a formal license is not needed to use this software.
* 
* This software is provided "AS IS."  
* NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
* OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
* AND DATA ACCURACY.  NIST does not warrant or make any representations
* regarding the use of the software or the results thereof, including but
* not limited to the correctness, accuracy, reliability or usefulness of
* this software.
*/
package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserScreen;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.ArrayList;
import java.util.logging.Level;
import java.util.logging.Logger;

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
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

public class DowloadData extends AbstractSpectrumBrowserScreen implements
		SpectrumBrowserCallback<String> {

	private SpectrumBrowser spectrumBrowser;
	private HorizontalPanel hpanel, urlPanel;
	private VerticalPanel verticalPanel;
	private MenuBar menuBar;
	private Button checkButton;
	private HTML title;
	private int dayCount;
	private long tSelectedStartTime, subBandMinFreq, subBandMaxFreq;
	private String sensorId, sys2detect;
	private String END_LABEL = "Download Data";
	private ArrayList<SpectrumBrowserScreen> navigation;

	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	public DowloadData(String sensorId, long tSelectedStartTime, int dayCount,
			String sys2detect, long minFreq, long maxFreq,
			VerticalPanel verticalPanel, SpectrumBrowser spectrumBrowser,
			ArrayList<SpectrumBrowserScreen> navigation) {
		super.setNavigation(verticalPanel, navigation, spectrumBrowser,
				END_LABEL);
		this.navigation = new ArrayList<SpectrumBrowserScreen>(navigation);
		this.navigation.add(this);
		this.spectrumBrowser = spectrumBrowser;
		this.verticalPanel = verticalPanel;
		this.dayCount = dayCount;
		this.tSelectedStartTime = tSelectedStartTime;
		this.sensorId = sensorId;
		this.sys2detect = sys2detect;
		spectrumBrowser.getSpectrumBrowserService().generateZipFileForDownload(
				sensorId, tSelectedStartTime, dayCount, sys2detect, minFreq,
				maxFreq, this);
	}

	public void draw() {
		verticalPanel.clear();
		super.drawNavigation();
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
					.checkForDumpAvailability(sensorId, uri, this);

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
				if (hpanel != null)
					hpanel.setVisible(false);
				urlPanel.clear();
				HTML html = new HTML("<a href=\"" + url + "\">" + url + "</a>");
				urlPanel.add(html);
			} else {
				urlPanel.clear();
				HTML html = new HTML(
						"<h4> Data availability pending. Link will appear when data is ready. Thank you for your patience. </h4>");
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
			String status = jsonObject.get("status").isString().stringValue();
			if (status.equals("NOK")) {
				Window.alert("No data in specified range");
				return;
			}
			final String uri = jsonObject.get("dump").isString().stringValue();
			String url = jsonObject.get("url").isString().stringValue();
			logger.finer("URL for data " + url);
			checkButton = new Button("Click to check for data availability");
			checkButton.addClickHandler(new CheckForDataAvailability(uri, url));
			title = new HTML("<h2>Bundling requested data</h2>");
			verticalPanel.add(title);
			verticalPanel.add(checkButton);

			urlPanel = new HorizontalPanel();
			verticalPanel.add(urlPanel);
			
			/*
			 * If user logged in we can mail him a notification.
			 */

			if (spectrumBrowser.getLoginEmailAddress() != null) {
				hpanel = new HorizontalPanel();
				Label label1 = new Label("Email notification to "+ spectrumBrowser.getLoginEmailAddress());
				hpanel.add(label1);
				Button submitButton = new Button();
				submitButton.setStyleName("sendButton");
				submitButton.setText("Submit");
				hpanel.add(submitButton);
				submitButton.addClickHandler(new ClickHandler() {
					@Override
					public void onClick(ClickEvent event) {
						spectrumBrowser.getSpectrumBrowserService()
								.emailUrlToUser(sensorId, uri,
										spectrumBrowser.getLoginEmailAddress(),
										new SpectrumBrowserCallback<String>() {

											@Override
											public void onSuccess(String result) {
												JSONValue jsonValue = JSONParser
														.parseLenient(result);
												String status = jsonValue
														.isObject()
														.get("status")
														.isString()
														.stringValue();
												if (status.equals("OK")) {
													Window.alert("Check your email for notification");
													navigateToPreviousScreen();
												} else {
													Window.alert("Please register if you want email notification");
												}

											}

											@Override
											public void onFailure(
													Throwable throwable) {
												Window.alert("Error communicating with server");

											}
										});

					}

				});
				verticalPanel.add(hpanel);
			}

		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Error parsing json file ", th);
		}

	}

	@Override
	public void onFailure(Throwable throwable) {
		Window.alert("Error contacting web service");
	}

}
