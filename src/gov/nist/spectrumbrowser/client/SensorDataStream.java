package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;

import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.canvas.client.Canvas;
import com.google.gwt.canvas.dom.client.Context2d;
import com.google.gwt.canvas.dom.client.Context2d.TextAlign;
import com.google.gwt.canvas.dom.client.CssColor;
import com.google.gwt.core.client.JsArray;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.googlecode.gwt.charts.client.ChartLoader;
import com.googlecode.gwt.charts.client.ChartPackage;
import com.googlecode.gwt.charts.client.ColumnType;
import com.googlecode.gwt.charts.client.DataTable;
import com.googlecode.gwt.charts.client.DataView;
import com.googlecode.gwt.charts.client.Selection;
import com.googlecode.gwt.charts.client.corechart.ScatterChart;
import com.googlecode.gwt.charts.client.corechart.ScatterChartOptions;
import com.googlecode.gwt.charts.client.event.SelectEvent;
import com.googlecode.gwt.charts.client.event.SelectHandler;
import com.googlecode.gwt.charts.client.options.HAxis;
import com.googlecode.gwt.charts.client.options.Legend;
import com.googlecode.gwt.charts.client.options.LegendPosition;
import com.googlecode.gwt.charts.client.options.VAxis;
import com.sksamuel.gwt.websockets.Websocket;
import com.sksamuel.gwt.websockets.WebsocketListenerExt;

public class SensorDataStream implements WebsocketListenerExt,
		SpectrumBrowserScreen {

	private static int STATUS_MESSAGE_NOT_SEEN = 1;
	private static int STATUS_MESSAGE_SEEN = 2;
	private static int DATA_MESSAGE_SEEN = 3;
	private String sensorId;
	private Websocket websocket;
	private VerticalPanel verticalPanel;
	private SpectrumBrowser spectrumBrowser;
	private SpectrumBrowserShowDatasets spectrumBrowserShowDatasets;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private JSONValue dataMessage;
	private int state = STATUS_MESSAGE_NOT_SEEN;
	private int canvasWidth = 800;
	private int canvasHeight = 280;
	private double minPower = -80.0;
	private double maxPower = 0;
	private ColorMap colorMap;
	private Canvas spectrogramCanvas;
	Canvas spectrogramFragment = null;
	int nFrequencyBins = 0;
	double minFreq;
	double maxFreq;
	int cutoff = 0;
	Context2d context2d;
	Canvas frequencyValuesCanvas = null;
	ScatterChart occupancyPlot;
	ScatterChartOptions occupancyPlotOptions;
	DataTable occupancyDataTable;
	DataTable spectrumDataTable;
	ScatterChart spectrumPlot;
	ScatterChartOptions spectrumPlotOptions;
	boolean chartApiLoaded = false;
	long counter = 0;
	private HorizontalPanel occupancyPanel;
	private HorizontalPanel spectrumPanel;
	private TextBox cutoffTextBox;
	private ArrayList<int[]> powerValuesList = new ArrayList<int[]>();
	boolean isFrozen = false;
	HTML html;
	VerticalPanel titlePanel;

	private static final String END_LABEL = "Sensor Data Stream";

	private static final double spectralColors[] = { 0.0, 0.0, 0.0,
			0.470205263158, 0.0, 0.536810526316, 0.477163157895, 0.0,
			0.607021052632, 0.0, 0.0, 0.698278947368, 0.0, 0.0982526315789,
			0.8667, 0.0, 0.501778947368, 0.8667, 0.0, 0.621063157895,
			0.803542105263, 0.0, 0.6667, 0.617552631579, 0.0, 0.638615789474,
			0.308752631579, 0.0, 0.663142105263, 0.0, 0.0, 0.803510526316, 0.0,
			0.0, 0.943873684211, 0.0, 0.463136842105, 1.0, 0.0, 0.870142105263,
			0.954363157895, 0.0, 0.982447368421, 0.835078947368, 0.0, 1.0,
			0.642105263158, 0.0, 1.0, 0.0947368421053, 0.0, 0.880731578947,
			0.0, 0.0, 0.803510526316, 0.0, 0.0, 0.8, 0.8, 0.8 };

	private static final double hotColors[] = { 0.0416, 0.0, 0.0,
			0.179767643888, 0.0, 0.0, 0.317935287777, 0.0, 0.0, 0.456102931665,
			0.0, 0.0, 0.594270575554, 0.0, 0.0, 0.732438219442, 0.0, 0.0,
			0.870605863331, 0.0, 0.0, 1.0, 0.00877287390197, 0.0, 1.0,
			0.146930544133, 0.0, 1.0, 0.285088214363, 0.0, 1.0, 0.423245884594,
			0.0, 1.0, 0.561403554824, 0.0, 1.0, 0.699561225055, 0.0, 1.0,
			0.837718895286, 0.0, 1.0, 0.975876565516, 0.0, 1.0, 1.0,
			0.171051802631, 1.0, 1.0, 0.378288851973, 1.0, 1.0, 0.585525901315,
			1.0, 1.0, 0.792762950658, 1.0, 1.0, 1.0 };

	double[] rainbow = { 0.5, 0.0, 1.0, 0.394736842105, 0.164594590281,
			0.996584493007, 0.289473684211, 0.324699469205, 0.986361303403,
			0.184210526316, 0.475947393037, 0.969400265939, 0.0789473684211,
			0.61421271269, 0.945817241701, 0.0263157894737, 0.735723910673,
			0.915773326655, 0.131578947368, 0.837166478263, 0.879473751206,
			0.236842105263, 0.915773326655, 0.837166478263, 0.342105263158,
			0.969400265939, 0.789140509396, 0.447368421053, 0.996584493007,
			0.735723910673, 0.552631578947, 0.996584493007, 0.677281571626,
			0.657894736842, 0.969400265939, 0.61421271269, 0.763157894737,
			0.915773326655, 0.546948158122, 0.868421052632, 0.837166478263,
			0.475947393037, 0.973684210526, 0.735723910673, 0.401695424653,
			1.0, 0.61421271269, 0.324699469205, 1.0, 0.475947393037,
			0.245485487141, 1.0, 0.324699469205, 0.164594590281, 1.0,
			0.164594590281, 0.0825793454723, 1.0, 1.22464679915e-16,
			6.12323399574e-17 };

	double[] monochrome = { 0, 0.5, 0, 0, 0.525, 0, 0, 0.55, 0, 0, 0.575, 0, 0,
			0.6, 0, 0, 0.625, 0, 0, 0.65, 0, 0, 0.675, 0, 0, 0.7, 0, 0, 0.725,
			0, 0, 0.75, 0, 0, 0.775, 0, 0, 0.8, 0, 0, 0.825, 0, 0, 0.85, 0, 0,
			0.875, 0, 0, 0.9, 0, 0, 0.925, 0, 0, 0.95, 0, 0, 0.975, 0, 0, 1, 0 };
	private float timeResolution;
	private Button freezeButton;
	private Button lastCaptureButton;
	private String sys2detect;
	private long minFreqHz;
	private long maxFreqHz;

	private class ColorStop {
		private double stopValue;
		private CssColor cssColor;

		ColorStop(double stopValue, CssColor cssColor) {
			this.stopValue = stopValue;
			this.cssColor = cssColor;
		}
	}

	private class ColorMap {

		LinkedList<ColorStop> colorList = new LinkedList<ColorStop>();

		double[] myColors = spectralColors;

		ColorMap(int max, int min) {
			int len = myColors.length / 3;
			for (int i = 0; i < len; i++) {
				double stopPosition = min + (double) (max - min) / (double) len
						* i;
				int red = (int) (255 * myColors[3 * i]);
				int green = (int) (255 * myColors[3 * i + 1]);
				int blue = (int) (255 * myColors[3 * i + 2]);
				addColorStop(stopPosition, CssColor.make(red, green, blue));
			}
		}

		private void addColorStop(double stop, CssColor cssColor) {
			logger.finer("addColorStop " + stop + " color " + cssColor.value());
			ColorStop cstop = new ColorStop(stop, cssColor);
			colorList.add(cstop);
		}

		private CssColor getColor(int value) {
			// Under cutoff gets grey color
			if (value < cutoff) {
				return CssColor.make("#A9A9A9");
			}
			for (ColorStop cs : colorList) {
				if (cs.stopValue > value) {
					return cs.cssColor;
				}
			}

			return CssColor.make(0, 0, 0);
		}

		List<ColorStop> getColorStops() {
			return colorList;
		}

		int getColorStopCount() {
			return colorList.size();
		}
	}

	native String btoa(String b64) /*-{
									return btoa(b64);
									}-*/;

	native String atob(String b64) /*-{
									return atob(b64);
									}-*/;

	private void drawMenuItems() {
		MenuBar menuBar = new MenuBar();
		SafeHtmlBuilder safeHtml = new SafeHtmlBuilder();

		menuBar.addItem(
				new SafeHtmlBuilder().appendEscaped(
						SpectrumBrowserShowDatasets.END_LABEL).toSafeHtml(),
				new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {
						websocket.close();
						spectrumBrowserShowDatasets.draw();
					}
				});
		menuBar.addItem(safeHtml.appendEscaped(SpectrumBrowser.LOGOFF_LABEL)
				.toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {
				websocket.close();
				spectrumBrowser.logoff();

			}
		});

		verticalPanel.add(menuBar);

		titlePanel = new VerticalPanel();

		verticalPanel.add(titlePanel);

		HorizontalPanel cutoffHorizontalPanel = new HorizontalPanel();

		Label cutoffLabel = new Label("Threshold (DBm):");

		cutoffHorizontalPanel.add(cutoffLabel);

		cutoffTextBox = new TextBox();

		cutoffTextBox.setText(Integer.toString((int) cutoff));

		cutoffHorizontalPanel.add(cutoffTextBox);

		Button cutoffButton = new Button("Change");

		cutoffHorizontalPanel.add(cutoffButton);

		cutoffButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				String cutoffString = cutoffTextBox.getValue();
				try {
					cutoff = Integer.parseInt(cutoffString);
				} catch (NumberFormatException nfe) {
					Window.alert("Please enter an integer");
				}

			}
		});

		freezeButton = new Button("Freeze");

		freezeButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {

				isFrozen = !isFrozen;
				if (isFrozen) {
					freezeButton.setText("Unfreeze");
				} else {
					freezeButton.setText("Freeze");
				}
			}
		});
		cutoffHorizontalPanel.add(freezeButton);

		lastCaptureButton = new Button("Show Last Capture");

		cutoffHorizontalPanel.add(lastCaptureButton);

		lastCaptureButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				spectrumBrowser.getSpectrumBrowserService()
						.getLastAcquisitionTime(spectrumBrowser.getSessionId(),
								sensorId,
								new SpectrumBrowserCallback<String>() {

									@Override
									public void onSuccess(String result) {
										JSONValue jsonValue = JSONParser
												.parseLenient(result);
										websocket.close();
										final long selectionTime = (long) jsonValue
												.isObject()
												.get("aquisitionTimeStamp")
												.isNumber().doubleValue();
										if (selectionTime != -1) {
											chartApiLoaded = false;
											occupancyDataTable = null;
											websocket.close();
											state = STATUS_MESSAGE_NOT_SEEN;
											isFrozen = false;
											Timer timer = new Timer() {
												@Override
												public void run() {
													
													ArrayList<SpectrumBrowserScreen> navigation = new ArrayList<SpectrumBrowserScreen>();
													navigation.add(spectrumBrowserShowDatasets);
													navigation.add(SensorDataStream.this);
													new FftPowerOneAcquisitionSpectrogramChart(
															sensorId,
															selectionTime,
															sys2detect,
															minFreqHz,
															maxFreqHz,
															verticalPanel,
															spectrumBrowser,
															navigation,
															SpectrumBrowser.MAP_WIDTH,
															SpectrumBrowser.MAP_HEIGHT)
															.draw();
												}
											};
											// Wait for websocket to close.
											timer.schedule(500);
										}
									}

									@Override
									public void onFailure(Throwable throwable) {
										logger.log(Level.SEVERE,
												"Problem contacting web server.");
										Window.alert("Problem contacting web server");
									}
								});
			}
		});

		verticalPanel.add(cutoffHorizontalPanel);

	}

	private float round(double val) {
		return (float) ((int)( (val + .05)* 10) / 10.0);
	}
	
	private float round3(double val) {
		return (float) ((int)( (val + .0005)* 1000) / 1000.0);

	}

	public SensorDataStream(String id, final VerticalPanel verticalPanel,
			SpectrumBrowser spectrumBrowser,
			SpectrumBrowserShowDatasets spectrumBrowserShowDatasets) {
		try {
			this.sensorId = id;
			this.verticalPanel = verticalPanel;
			this.spectrumBrowser = spectrumBrowser;
			this.spectrumBrowserShowDatasets = spectrumBrowserShowDatasets;

		} catch (Throwable th) {
			logger.log(Level.SEVERE, "ERROR setting up streaming", th);

		}

	}

	@Override
	public void onClose() {
		logger.fine("websocket.onClose");
		// state = STATUS_MESSAGE_NOT_SEEN;
		// spectrumBrowserShowDatasets.buildUi();
	}

	@Override
	public void onMessage(String msg) {
		// int nSpectrums;
		double xScale = 4;
		double yScale = 0;
		try {
			if (state == STATUS_MESSAGE_NOT_SEEN) {
				JSONValue statusMessage = JSONParser.parseLenient(msg);
				JSONObject jsonObj = statusMessage.isObject();
				if (jsonObj.get("status").isString().stringValue()
						.equals("NO_DATA")) {

					Window.alert("NO Data Available");
					websocket.close();
					spectrumBrowserShowDatasets.draw();
				} else if (jsonObj.get("status").isString().stringValue()
						.equals("OK")) {
					state = STATUS_MESSAGE_SEEN;
				}
			} else if (state == STATUS_MESSAGE_SEEN) {

				dataMessage = JSONParser.parseLenient(msg);
				logger.finer("msg = " + msg);
				JSONObject mpar = dataMessage.isObject().get("mPar").isObject();
				nFrequencyBins = (int) mpar.get("n").isNumber().doubleValue();
				// The default cutoff value (add 2 to the noise floor).
				cutoff = (int) dataMessage.isObject().get("wnI").isNumber()
						.doubleValue() + 2;
				cutoffTextBox.setText(Integer.toString(cutoff));
				logger.finer("n = " + nFrequencyBins);
				minFreqHz = (long) mpar.get("fStart").isNumber().doubleValue();
				maxFreqHz = (long) mpar.get("fStop").isNumber().doubleValue();
				minFreq = (mpar.get("fStart").isNumber().doubleValue() / 1E6);
				maxFreq = mpar.get("fStop").isNumber().doubleValue() / 1E6;
				sys2detect = dataMessage.isObject().get("Sys2Detect")
						.isString().stringValue();

				// For computing the occupancy, determine the cutoff.

				logger.finer("fStart / fStop = " + Double.toString(minFreq)
						+ " " + Double.toString(maxFreq));
				Context2d ctx = frequencyValuesCanvas.getContext2d();
				ctx.setTextAlign(TextAlign.LEFT);
				ctx.fillText(Double.toString(maxFreq), 0, 10, 100);
				ctx.fillText("Freq (MHz)", 0, canvasHeight / 2 - 4, 100);
				ctx.fillText(Double.toString(minFreq), 0, canvasHeight - 4, 100);
				spectrogramFragment = Canvas.createIfSupported();
				spectrogramFragment.setWidth(canvasWidth + "px");
				spectrogramFragment.setHeight(canvasHeight + "px");
				spectrogramFragment.setCoordinateSpaceHeight(canvasWidth);
				spectrogramFragment.setCoordinateSpaceHeight(canvasHeight);
				spectrogramFragment.getCanvasElement().setWidth(canvasWidth);
				spectrogramFragment.getCanvasElement().setHeight(canvasHeight);
				state = DATA_MESSAGE_SEEN;
				context2d.setFillStyle(CssColor.make("black"));
				context2d.fillRect(0, 0, canvasWidth, canvasHeight);
				spectrogramFragment.setVisible(false);
				double timePerMeasurement = (float) mpar.get("tm").isNumber()
						.doubleValue();
				timeResolution = (float) (dataMessage.isObject()
						.get("spectrumsPerFrame").isNumber().doubleValue() * timePerMeasurement);
				HTML html = new HTML("<h2>Sensor Data Stream for " + sensorId 
						+ "</h2>");
				titlePanel.add(html);
				HTML help = new HTML(
						"<p>Click on spectrogram to freeze/unfreze. "
								+ "Click on occupancy point to show spectrum</p>");
				titlePanel.add(help);
				String filter = dataMessage.isObject().get("StreamingFilter")
						.isString().stringValue();
				float freqResolution = round((float) (maxFreq - minFreq)
						/ nFrequencyBins * 1000);
				html = new HTML("<h3>Freq resolution = " + freqResolution 
						+ " kHz. ;Detected System = " + sys2detect + "; Time resoultion = " + timeResolution
						+ " sec. Filter = " + filter + " </h3>");
				titlePanel.add(html);
			} else if (state == DATA_MESSAGE_SEEN) {
				String[] values = msg.split(",");
				int powerValues[] = new int[values.length];

				int occupancyCount = 0;
				for (int i = 0; i < values.length; i++) {
					powerValues[i] = Integer.parseInt(values[i].trim());
					if (powerValues[i] > cutoff) {
						occupancyCount++;
					}
				}

				float occupancy = round(((double) occupancyCount / (double) values.length) * 100);
				int nSpectrums = (int) (canvasWidth / xScale);

				if (chartApiLoaded && occupancyDataTable == null) {
					occupancyDataTable = DataTable.create();
					spectrumDataTable = DataTable.create();
					occupancyPlotOptions = ScatterChartOptions.create();
					occupancyPlotOptions.setBackgroundColor("#f0f0f0");
					occupancyPlotOptions.setPointSize(5);
					occupancyPlotOptions.setHAxis(HAxis.create("Time (sec)"));
					VAxis vaxis = VAxis.create("Occupancy %");
					vaxis.setMaxValue(100.0);
					vaxis.setMinValue(0);
					occupancyPlotOptions.setVAxis(vaxis);
					Legend legend = Legend.create();
					legend.setPosition(LegendPosition.NONE);
					occupancyPlotOptions.setLegend(legend);
					spectrumPlotOptions = ScatterChartOptions.create();
					spectrumPlotOptions.setBackgroundColor("#f0f0f0");
					spectrumPlotOptions.setPointSize(5);
					spectrumPlotOptions.setHAxis(HAxis
							.create("Frequency (MHz)"));
					spectrumPlotOptions.setVAxis(VAxis.create("Power (dBm)"));

					legend = Legend.create();
					legend.setPosition(LegendPosition.NONE);
					spectrumPlotOptions.setLegend(legend);
					occupancyPlot = new ScatterChart();

					spectrumPlot = new ScatterChart();
					occupancyPlot.addSelectHandler(new SelectHandler() {

						@Override
						public void onSelect(SelectEvent event) {

							if (!isFrozen) {
								logger.finer("Please Freeze canvas before clicking");
								return;
							} else {
								JsArray<Selection> selection = occupancyPlot
										.getSelection();
								int length = selection.length();
								int row = selection.get(0).getRow();
								logger.finer("Selected row" + row);
								int[] spectrumData = powerValuesList.get(row);
								double mhzPerDivision = (maxFreq - minFreq)
										/ spectrumData.length;
								for (int i = 0; i < spectrumData.length; i++) {
									double freq = minFreq + mhzPerDivision * i;
									spectrumDataTable.setCell(i, 0, freq, freq + " Mhz");
									spectrumDataTable.setCell(i, 1, spectrumData[i], spectrumData[i] + " dBm");
								}
								spectrumPlot.draw(spectrumDataTable,
										spectrumPlotOptions);
							}

						}
					});

					occupancyPlot.setPixelSize(canvasWidth + 260, canvasHeight);
					occupancyPlot.setTitle("Occupancy");
					spectrumPlot.setPixelSize(canvasWidth + 260, canvasHeight);
					occupancyPanel.add(occupancyPlot);
					spectrumPanel.add(spectrumPlot);
					occupancyDataTable.addColumn(ColumnType.NUMBER,
							"Time (sec)");
					occupancyDataTable.addColumn(ColumnType.NUMBER,
							"Occupancy %");
					spectrumDataTable.addColumn(ColumnType.NUMBER,
							"Frequency (MHz)");
					spectrumDataTable.addColumn(ColumnType.NUMBER,
							"Power (milliwatts)");
					spectrumDataTable.setColumnLabel(0, "Frequency (MHz)");
					spectrumDataTable.setColumnLabel(1, "Power (mw)");
					occupancyDataTable.addRows(nSpectrums);
					spectrumDataTable.addRows(powerValues.length);

					DataView dataView = DataView.create(occupancyDataTable);

					for (int i = 0; i < nSpectrums; i++) {
						occupancyDataTable.setCell(i, 0,round3( i * timeResolution),round3( i * timeResolution) + " sec");
						occupancyDataTable.setCell(i, 1, 0, "0 % occupancy");
						occupancyPlot.draw(dataView, occupancyPlotOptions);

					}
					// Initialize the spectrum list
					for (int i = 0; i < nSpectrums; i++) {
						int[] dummyValues = new int[values.length];
						for (int j = 0; j < dummyValues.length; j++) {
							dummyValues[j] = 0;
						}
						powerValuesList.add(dummyValues);
					}
					counter = nSpectrums - 1;
				}

				if (!isFrozen) {

					if (occupancyDataTable != null) {
						occupancyDataTable.removeRow(0);
						occupancyDataTable.addRow();
						int rowCount = occupancyDataTable.getNumberOfRows();
						counter++;
						for (int i = 0; i < nSpectrums; i++) {
							occupancyDataTable.setCell(i, 0, round3(i
									* timeResolution),round3(i
											* timeResolution) + " sec");
						}
						occupancyDataTable.setCell(rowCount - 1, 1,occupancy, occupancy + " % occupancy");
						occupancyPlot.redraw();
						powerValuesList.remove(0);
						powerValuesList.add(powerValues);
						// occupancyPlot.draw(dataTable);
					}

					context2d.save();
					Context2d tempContext = spectrogramFragment.getContext2d();
					tempContext.drawImage(spectrogramCanvas.getCanvasElement(),
							0, 0, (double) canvasWidth, (double) canvasHeight);
					RootPanel.get().add(spectrogramFragment);

					// nSpectrums = powerValues.length / nFrequencyBins;
					yScale = (double) canvasHeight / (double) nFrequencyBins;
					for (int i = 0; i < powerValues.length; i++) {
						CssColor color = colorMap.getColor(powerValues[i]);
						int row = (int) ((i % nFrequencyBins) * yScale);
						int col = (int) ((i / nFrequencyBins) * xScale);

						context2d.setFillStyle(color);
						double x = canvasWidth - col - xScale;
						double y = canvasHeight - row - yScale;
						double w = xScale;
						double h = yScale;
						context2d.fillRect(x, y, w, h);

					}

					context2d.translate(-xScale, 0);
					context2d.drawImage(spectrogramFragment.getCanvasElement(),
							0, 0, spectrogramFragment.getCanvasElement()
									.getWidth(), spectrogramFragment
									.getCanvasElement().getHeight(), 0, 0,
							canvasWidth, canvasHeight);
					// reset the transformation matrix
					context2d.setTransform(1, 0, 0, 1, 0, 0);
					RootPanel.get().remove(spectrogramFragment);
				}
			}
		} catch (Throwable ex) {
			logger.log(Level.SEVERE, "ERROR parsing data", ex);
		}

	}

	@Override
	public void onOpen() {
		logger.finer("onOpen");
		String sid = spectrumBrowser.getSessionId();
		String token = sid + ":" + sensorId;
		websocket.send(token);
	}

	@Override
	public void onError() {
		logger.info("Web Socket Error");
		websocket.close();
		try {
			openWebSocket();
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Could not re-open websocket", th);
			Window.alert("Websocket Error communicating with server");
			spectrumBrowserShowDatasets.draw();
		}
		
	}

	@Override
	public void draw() {
		try {
			// TODO Auto-generated method stub
			verticalPanel.clear();
			drawMenuItems();
			verticalPanel.setTitle("Click on canvas to freeze/unfreeze");

			HorizontalPanel spectrogramPanel = new HorizontalPanel();

			int minPower = -80;
			int maxPower = -40;
			colorMap = new ColorMap(maxPower, minPower);

			verticalPanel.add(spectrogramPanel);

			frequencyValuesCanvas = Canvas.createIfSupported();
			frequencyValuesCanvas.setWidth(100 + "px");
			frequencyValuesCanvas.setHeight(canvasHeight + "px");
			frequencyValuesCanvas.setCoordinateSpaceHeight(canvasHeight);
			frequencyValuesCanvas.setCoordinateSpaceWidth(100);

			spectrogramCanvas = Canvas.createIfSupported();
			spectrogramCanvas.setWidth(canvasWidth + "px");
			spectrogramCanvas.setHeight(canvasHeight + "px");
			spectrogramCanvas.setCoordinateSpaceWidth(canvasWidth);
			spectrogramCanvas.setCoordinateSpaceHeight(canvasHeight);
			spectrogramCanvas.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent event) {
					isFrozen = !isFrozen;
					if (isFrozen) {
						freezeButton.setText("Unfreeze");
					} else {
						freezeButton.setText("Freeze");
					}
				}
			});
			spectrogramPanel.add(frequencyValuesCanvas);
			spectrogramPanel.add(spectrogramCanvas);
			spectrogramPanel.setBorderWidth(3);
			// Draw the colorbar canvas.
			HorizontalPanel colorbarFrame = new HorizontalPanel();
			colorbarFrame.setBorderWidth(3);
			Canvas colorbarCanvas = Canvas.createIfSupported();
			Canvas colorbarTextCanvas = Canvas.createIfSupported();
			colorbarCanvas.setWidth(30 + "px");
			colorbarCanvas.setCoordinateSpaceHeight(canvasHeight);
			colorbarCanvas.setCoordinateSpaceWidth(30);
			colorbarTextCanvas.setWidth(30 + "px");
			colorbarCanvas.setHeight(canvasHeight + "px");
			colorbarTextCanvas.setCoordinateSpaceHeight(canvasHeight);
			colorbarTextCanvas.setHeight(canvasHeight + "px");
			colorbarTextCanvas.setCoordinateSpaceWidth(30);
			int nStops = colorMap.getColorStopCount();
			colorbarFrame.add(colorbarCanvas);
			colorbarFrame.add(colorbarTextCanvas);
			spectrogramPanel.add(colorbarFrame);
			verticalPanel.add(spectrogramPanel);
			double rectHeight = (double) canvasHeight / (double) nStops;
			int i = 0;
			for (ColorStop colorStop : colorMap.getColorStops()) {
				CssColor color = colorStop.cssColor;
				Context2d context = colorbarCanvas.getContext2d();
				context.setFillStyle(color);
				double y = canvasHeight - (i + 1) * rectHeight;
				context.fillRect(0, y, 30, (int) rectHeight);
				Context2d textContext = colorbarTextCanvas.getContext2d();
				textContext.setTextAlign(TextAlign.LEFT);
				textContext.fillText(
						Integer.toString((int) colorStop.stopValue), 0,
						(int) (y + rectHeight / 2));
				i++;
			}

			occupancyPanel = new HorizontalPanel();
			VerticalPanel pad = new VerticalPanel();
			pad.setWidth("25px");
			occupancyPanel.add(pad);
			spectrumPanel = new HorizontalPanel();
			ChartLoader chartLoader = new ChartLoader(ChartPackage.CORECHART);

			chartLoader.loadApi(new Runnable() {
				@Override
				public void run() {
					chartApiLoaded = true;

				}
			});
			verticalPanel.add(occupancyPanel);
			verticalPanel.add(spectrumPanel);

			context2d = spectrogramCanvas.getContext2d();
			openWebSocket();
		} catch (Throwable th) {
			logger.log(Level.SEVERE, "ERROR drawing screen", th);
		}
	}
	
	private void openWebSocket() {
		String authority = SpectrumBrowser.getBaseUrlAuthority();
		String url;
		if (authority.startsWith("https")) {
			url = authority.replace("https", "wss") + "/sensordata";
		} else {
			url = authority.replace("http", "ws") + "/sensordata";
		}
		logger.fine("Websocket URL " + url);
		websocket = new Websocket(url);
		websocket.addListener(this);
		if (!websocket.isSupported()) {
			Window.alert("Websockets not supported on this browser");
			spectrumBrowserShowDatasets.draw();
		} else {
			websocket.open();
		}
		
	}

	@Override
	public String getLabel() {
		return END_LABEL + " >>";
	}

	@Override
	public String getEndLabel() {
		return END_LABEL;
	}

}
