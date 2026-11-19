# frozen_string_literal: true

# Input comes from `brew bundle list --formula` and `brew info --json=v2
# --formula --installed`. Keep JSON parsing out of the shell startup files.
require "json"

manifest, inventory, prefix = ARGV
formulae = JSON.parse(File.read(inventory)).fetch("formulae")
paths = []

File.foreach(manifest, chomp: true) do |requested|
  next if requested.empty?

  formula = formulae.find do |entry|
    names = [entry.fetch("name"), entry.fetch("full_name"),
             *entry.fetch("aliases", []), *entry.fetch("oldnames", [])]
    tap = entry.fetch("tap")
    names.flat_map { |name| name.include?("/") ? [name] : [name, "#{tap}/#{name}"] }.include?(requested)
  end
  next unless formula && formula["keg_only"] && !formula.fetch("installed").empty?

  %w[bin sbin].each do |directory|
    candidate = File.join(prefix, "opt", formula.fetch("name"), directory)
    paths << candidate if File.directory?(candidate)
  end
end

puts paths.uniq
