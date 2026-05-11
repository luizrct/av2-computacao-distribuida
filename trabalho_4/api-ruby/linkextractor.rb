require "sinatra"
require "json"
require "open-uri"
require "nokogiri"
require "uri"
require "redis"

set :bind, "0.0.0.0"
set :port, 4567

USE_CACHE = ENV.fetch("USE_CACHE", "false").downcase == "true"
REDIS_URL = ENV["REDIS_URL"]

redis_client = USE_CACHE && REDIS_URL ? Redis.new(url: REDIS_URL) : nil

def extract_links(url)
  html = URI.open(url, read_timeout: 10).read
  document = Nokogiri::HTML(html)

  links = document.css("a[href]").map do |tag|
    href = tag["href"]
    URI.join(url, href).to_s
  rescue URI::InvalidURIError
    nil
  end

  links.compact.uniq.sort
end

get "/api/" do
  content_type :json

  url = params["url"]

  if url.nil? || url.strip.empty?
    status 400
    return {
      error: "Parâmetro 'url' é obrigatório."
    }.to_json
  end

  cache_key = "links:#{url}"

  if redis_client
    cached_value = redis_client.get(cache_key)

    unless cached_value.nil?
      return {
        url: url,
        links: JSON.parse(cached_value),
        cached: true,
        service: "ruby"
      }.to_json
    end
  end

  begin
    links = extract_links(url)

    if redis_client
      redis_client.set(cache_key, links.to_json, ex: 3600)
    end

    {
      url: url,
      links: links,
      cached: false,
      service: "ruby"
    }.to_json
  rescue StandardError => error
    status 500

    {
      url: url,
      error: error.message,
      service: "ruby"
    }.to_json
  end
end

get "/health" do
  content_type :json

  {
    status: "ok",
    service: "ruby"
  }.to_json
end