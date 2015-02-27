package gov.nist.spectrumbrowser.admin;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.logical.shared.ValueChangeEvent;
import com.google.gwt.event.logical.shared.ValueChangeHandler;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.CheckBox;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

public class SetStreamingParams {

	private Admin admin;
	private SensorConfig sensorConfig;
	private VerticalPanel verticalPanel;
	private Sensor sensor;
	private StreamingParams sensorStreamingParams;

	public SetStreamingParams(Admin admin, VerticalPanel verticalPanel,
			Sensor sensor, SensorConfig sensorConfig) {
		this.admin = admin;
		this.sensorConfig = sensorConfig;
		this.verticalPanel = verticalPanel;
		this.sensor = sensor;
		this.sensorStreamingParams = new StreamingParams(
				sensor.getStreamingConfig());
	}

	public void draw() {
		HTML html = new HTML("<h2>Streaming settings for "
				+ sensor.getSensorId() + "</h2>");
		verticalPanel.clear();
		verticalPanel.add(html);
		Grid grid = new Grid(5, 2);
		grid.setBorderWidth(2);
		grid.setCellPadding(2);
		grid.setCellSpacing(2);

		int row = 0;
		final TextBox streamingCaptureIntervalTextBox = new TextBox();
		streamingCaptureIntervalTextBox.setText(Integer
				.toString(sensorStreamingParams
						.getStreamingCaptureSamplingIntervalSeconds()));
		streamingCaptureIntervalTextBox
				.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						try {
							int streamingCaptureInterval = Integer
									.parseInt(event.getValue());
							if (!sensorStreamingParams
									.setStreamingCaptureSamplingIntervalSeconds(streamingCaptureInterval)) {
								Window.alert("Please enter a valid integer > 0");
								streamingCaptureIntervalTextBox.setValue(Integer.toString(sensorStreamingParams
										.getStreamingCaptureSamplingIntervalSeconds()));
							}
						} catch (Exception ex) {
							Window.alert("Please enter a valid integer >0");
							streamingCaptureIntervalTextBox.setValue(Integer.toString(sensorStreamingParams
									.getStreamingCaptureSamplingIntervalSeconds()));
						}
					}
				});
		grid.setText(row, 0, "Time between captures");
		grid.setWidget(row, 1, streamingCaptureIntervalTextBox);

		row++;
		final TextBox streamingCaptureSampleSizeTextBox = new TextBox();
		streamingCaptureSampleSizeTextBox.setText(Integer
				.toString(sensorStreamingParams
						.getStreamingCaptureSampleSizeSeconds()));
		streamingCaptureSampleSizeTextBox
				.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						try {
							int sampleSizeSeconds = Integer.parseInt(event
									.getValue());
							if (!sensorStreamingParams
									.setStreamingCaptureSampleSizeSeconds(sampleSizeSeconds)) {
								Window.alert("Please enter integer > 0");
								streamingCaptureSampleSizeTextBox.setValue(Integer.toString(sensorStreamingParams
										.getStreamingCaptureSampleSizeSeconds()));
							}
						} catch (Exception ex) {
							Window.alert("Please enter integer >0");
							streamingCaptureSampleSizeTextBox.setValue(Integer.toString(sensorStreamingParams
									.getStreamingCaptureSampleSizeSeconds()));
						}
					}
				});
		grid.setText(row, 0, "Spectrogram Capture Sample Size (s)");
		grid.setWidget(row, 1, streamingCaptureSampleSizeTextBox);
		streamingCaptureSampleSizeTextBox
				.setTitle("The time interval of the captured spectrogram.");

		row++;

		final CheckBox enableStreamingCapture = new CheckBox();
		enableStreamingCapture.setValue(sensorStreamingParams.getEnableStreamingCapture());
		grid.setText(row, 0, "Enable Streaming Capture");
		enableStreamingCapture
				.addValueChangeHandler(new ValueChangeHandler<Boolean>() {

					@Override
					public void onValueChange(ValueChangeEvent<Boolean> event) {
						boolean newValue = event.getValue();
						streamingCaptureIntervalTextBox.setEnabled(newValue);
						streamingCaptureSampleSizeTextBox.setEnabled(newValue);
						sensorStreamingParams.setEnableStreamingCapture(newValue);
					}
				});

		grid.setWidget(row, 1, enableStreamingCapture);
		
		row++;

		final TextBox streamingSecondsPerFrameTextBox = new TextBox();
		streamingSecondsPerFrameTextBox.setText(Float
				.toString(sensorStreamingParams.getStreamingSecondsPerFrame()));
		streamingSecondsPerFrameTextBox
				.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						try {
							float streamingSecondsPerFrame = Float
									.parseFloat(event.getValue());
							if (!sensorStreamingParams
									.setStreamingSecondsPerFrame(streamingSecondsPerFrame)) {
								Window.alert("Please set a float > 0");
								streamingSecondsPerFrameTextBox.setText(Float
										.toString(sensorStreamingParams
												.getStreamingSecondsPerFrame()));
							}

						} catch (Exception ex) {
							Window.alert(ex.getMessage());
							streamingSecondsPerFrameTextBox.setText(Float
									.toString(sensorStreamingParams
											.getStreamingSecondsPerFrame()));
						}
					}
				});

		grid.setText(row, 0, "Time Resolution Per Frame (s)");
		grid.setWidget(row, 1, streamingSecondsPerFrameTextBox);
		streamingSecondsPerFrameTextBox
				.setTitle("Size of the aggregation window frame periodically sent to the browser");

		row++;
		final TextBox streamingFilterTextBox = new TextBox();
		streamingFilterTextBox.setText(sensorStreamingParams
				.getStreamingFilter());
		streamingFilterTextBox
				.addValueChangeHandler(new ValueChangeHandler<String>() {

					@Override
					public void onValueChange(ValueChangeEvent<String> event) {
						String newFilter = event.getValue();
						if (!sensorStreamingParams
								.setStreamingFilter(newFilter)) {
							Window.alert("Please specify MAX_HOLD or MEAN");
							streamingFilterTextBox
									.setText(sensorStreamingParams
											.getStreamingFilter());
						}
					}
				});
		grid.setText(row, 0, "Aggregation Filter (MAX_HOLD or MEAN)");
		grid.setWidget(row, 1, streamingFilterTextBox);

		verticalPanel.add(grid);
		HorizontalPanel hpanel = new HorizontalPanel();
		Button applyButton = new Button("Apply");
		applyButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				if (!sensorStreamingParams.verify()) {
					Window.alert("Please specify all fields");
					return;
				} else {
					sensorConfig.setUpdateFlag(true);
					Admin.getAdminService().updateSensor(sensor.toString(),
							sensorConfig);
				}
			}
		});
		hpanel.add(applyButton);

		for (int i = 0; i < grid.getRowCount(); i++) {
			grid.getCellFormatter().setStyleName(i, 0, "textLabelStyle");
		}

		Button cancelButton = new Button("Cancel");
		cancelButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				sensorStreamingParams.restore();
				sensorConfig.draw();
			}
		});
		hpanel.add(cancelButton);

		Button clearButton = new Button("Clear");
		clearButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				sensorStreamingParams.clear();
				sensorConfig.setUpdateFlag(true);
				Admin.getAdminService().updateSensor(sensor.toString(),
						sensorConfig);
			}
		});
		hpanel.add(clearButton);

		Button logoffButton = new Button("Log Off");
		logoffButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}
		});
		hpanel.add(logoffButton);

		verticalPanel.add(hpanel);

	}

}
