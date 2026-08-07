"""Spiral-matrix task definitions for the four-topic 60-task batch."""

from __future__ import annotations

from .common import TaskSpec


_COORDS = r"""
static std::vector<std::pair<std::size_t,std::size_t>> order(
    std::size_t rows,std::size_t cols) {
    std::vector<std::pair<std::size_t,std::size_t>> out;
    if (rows==0 || cols==0) return out;
    std::size_t top=0,left=0,bottom=rows,right=cols;
    while (top<bottom && left<right) {
        for (std::size_t c=left;c<right;++c) out.push_back({top,c});
        ++top;
        --right;
        for (std::size_t r=top;r<bottom;++r) out.push_back({r,right});
        if (top<bottom) {
            --bottom;
            for (std::size_t c=right;c-- >left;) out.push_back({bottom,c});
        }
        if (left<right && top<bottom) {
            for (std::size_t r=bottom;r-- >top;) out.push_back({r,left});
            ++left;
        }
    }
    return out;
}
"""


SPECS = (
    TaskSpec(
        "spiral-cyclic-pattern-search",
        r"""
namespace spiral_pattern {
""" + _COORDS + r"""
std::vector<std::size_t> cyclic_matches(
    const std::vector<std::vector<int>>& grid,const std::vector<int>& pattern) {
    if (!grid.empty()) for (const auto& row:grid)
        if (row.size()!=grid.front().size()) throw std::invalid_argument("ragged");
    const auto coordinates=order(grid.size(),grid.empty()?0:grid.front().size());
    std::vector<std::size_t> out;
    if (coordinates.empty()) return out;
    if (pattern.empty()) {
        for (std::size_t i=0;i<coordinates.size();++i) out.push_back(i);
        return out;
    }
    for (std::size_t start=0;start<coordinates.size();++start) {
        bool same=true;
        for (std::size_t i=0;i<pattern.size();++i) {
            const auto [r,c]=coordinates[(start+i)%coordinates.size()];
            if (grid[r][c]!=pattern[i]) { same=false; break; }
        }
        if (same) out.push_back(start);
    }
    return out;
}
}
""",
        r"""
int main() {
    using spiral_pattern::cyclic_matches;
    std::vector<std::vector<int>> g{{1,2,3},{8,9,4},{7,6,5}};
    assert((cyclic_matches(g,{1,2,3})==std::vector<std::size_t>{0}));
    assert((cyclic_matches(g,{9,1})==std::vector<std::size_t>{8}));
    assert(cyclic_matches(g,{1,2,3,4,5,6,7,8,9,1}).size()==1);
    assert(cyclic_matches(g,{}).size()==9);
    assert(cyclic_matches({},{}).empty());
    bool bad=false; try { (void)cyclic_matches({{1},{2,3}},{1}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "(start+i)%coordinates.size()",
        "(start+i+1)%coordinates.size()",
        "cyclic-spiral-search",
        ("cyclic-pattern", "boundary-order", "wrapped-index"),
    ),
    TaskSpec(
        "spiral-permutation-cycles",
        r"""
namespace spiral_cycles {
""" + _COORDS + r"""
std::vector<std::vector<std::size_t>> cycles(std::size_t rows,std::size_t cols) {
    if (rows!=0 && cols>std::numeric_limits<std::size_t>::max()/rows)
        throw std::overflow_error("dimensions");
    const auto coordinates=order(rows,cols);
    std::vector<std::size_t> permutation(coordinates.size());
    for (std::size_t spiral=0;spiral<coordinates.size();++spiral)
        permutation[coordinates[spiral].first*cols+coordinates[spiral].second]=spiral;
    std::vector<bool> seen(permutation.size(),false);
    std::vector<std::vector<std::size_t>> out;
    for (std::size_t start=0;start<permutation.size();++start) if (!seen[start]) {
        std::vector<std::size_t> cycle;
        for (auto current=start;!seen[current];current=permutation[current]) {
            seen[current]=true; cycle.push_back(current);
        }
        if (cycle.size()>1) {
            auto minimum=std::min_element(cycle.begin(),cycle.end());
            std::rotate(cycle.begin(),minimum,cycle.end()); out.push_back(cycle);
        }
    }
    std::sort(out.begin(),out.end());
    return out;
}
}
""",
        r"""
int main() {
    using spiral_cycles::cycles;
    assert(cycles(0,4).empty());
    assert(cycles(1,4).empty());
    auto a=cycles(2,2); assert(a.size()==1 && a[0].front()==2);
    auto b=cycles(3,3); assert(!b.empty());
    for(const auto& cycle:b) assert(cycle.size()>1 && cycle.front()==*std::min_element(cycle.begin(),cycle.end()));
    auto c=cycles(2,3); assert(std::is_sorted(c.begin(),c.end()));
}
""",
        "if (cycle.size()>1)",
        "if (cycle.size()>=1)",
        "spiral-permutation",
        ("permutation-cycle", "row-major-map", "canonical-rotation"),
    ),
    TaskSpec(
        "spiral-run-codec",
        r"""
namespace spiral_rle {
""" + _COORDS + r"""
std::vector<Run> encode(const std::vector<std::vector<int>>& grid) {
    if (!grid.empty()) for (const auto& row:grid)
        if (row.size()!=grid.front().size()) throw std::invalid_argument("ragged");
    std::vector<Run> out;
    for (const auto& [r,c]:order(grid.size(),grid.empty()?0:grid.front().size())) {
        if (!out.empty() && out.back().value==grid[r][c]) ++out.back().length;
        else out.push_back({grid[r][c],1});
    }
    return out;
}
std::vector<std::vector<int>> decode(
    std::size_t rows,std::size_t cols,const std::vector<Run>& runs) {
    if (rows!=0 && cols>std::numeric_limits<std::size_t>::max()/rows)
        throw std::overflow_error("dimensions");
    std::vector<int> values;
    for (std::size_t i=0;i<runs.size();++i) {
        if (runs[i].length==0 || (i && runs[i-1].value==runs[i].value))
            throw std::invalid_argument("runs");
        if (runs[i].length>rows*cols-values.size()) throw std::invalid_argument("total");
        values.insert(values.end(),runs[i].length,runs[i].value);
    }
    if (values.size()!=rows*cols) throw std::invalid_argument("total");
    std::vector<std::vector<int>> grid(rows,std::vector<int>(cols));
    const auto coordinates=order(rows,cols);
    for (std::size_t i=0;i<values.size();++i)
        grid[coordinates[i].first][coordinates[i].second]=values[i];
    return grid;
}
}
""",
        r"""
int main() {
    using spiral_rle::encode; using spiral_rle::decode;
    std::vector<std::vector<int>> g{{1,1,2},{3,3,2}};
    auto runs=encode(g); assert(runs.size()==3 && runs[0].length==2);
    assert(decode(2,3,runs)==g);
    assert(encode({}).empty());
    assert(decode(0,3,{}).empty());
    bool bad=false; try { (void)decode(1,2,{{1,1},{1,1}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
    bad=false; try { (void)decode(2,2,{{1,3}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "if (values.size()!=rows*cols)",
        "if (values.size()>rows*cols)",
        "spiral-run-codec",
        ("run-length", "scatter", "rectangular"),
    ),
    TaskSpec(
        "spiral-prefix-index",
        r"""
namespace spiral_prefix {
struct State {
    std::size_t rows=0,cols=0;
    std::vector<std::int64_t> values;
    std::vector<std::size_t> position;
};
static std::map<const Index*,State> states;
static std::vector<std::pair<std::size_t,std::size_t>> make_order(
    std::size_t rows,std::size_t cols) {
    std::vector<std::pair<std::size_t,std::size_t>> out;
    if (!rows || !cols) return out;
    std::size_t top=0,left=0,bottom=rows,right=cols;
    while(top<bottom && left<right) {
        for(std::size_t c=left;c<right;++c) out.push_back({top,c});
        ++top;
        --right;
        for(std::size_t r=top;r<bottom;++r) out.push_back({r,right});
        if(top<bottom){--bottom;for(std::size_t c=right;c-- >left;)out.push_back({bottom,c});}
        if(left<right && top<bottom){
            for(std::size_t r=bottom;r-- >top;) out.push_back({r,left});
            ++left;
        }
    }
    return out;
}
Index::Index(std::vector<std::vector<std::int64_t>> grid) {
    if (!grid.empty()) for(const auto& row:grid)
        if(row.size()!=grid.front().size()) throw std::invalid_argument("ragged");
    State state; state.rows=grid.size(); state.cols=grid.empty()?0:grid.front().size();
    state.position.resize(state.rows*state.cols);
    const auto coordinates=make_order(state.rows,state.cols);
    for(std::size_t i=0;i<coordinates.size();++i) {
        const auto [r,c]=coordinates[i]; state.values.push_back(grid[r][c]);
        state.position[r*state.cols+c]=i;
    }
    states[this]=std::move(state);
}
std::int64_t Index::range_sum(std::size_t first,std::size_t last) const {
    const auto& values=states.at(this).values;
    if(first>last || last>=values.size()) throw std::out_of_range("range");
    return std::accumulate(values.begin()+static_cast<std::ptrdiff_t>(first),
                           values.begin()+static_cast<std::ptrdiff_t>(last+1),std::int64_t{0});
}
void Index::update(std::size_t row,std::size_t col,std::int64_t value) {
    auto& state=states.at(this);
    if(row>=state.rows || col>=state.cols) throw std::out_of_range("coordinate");
    state.values[state.position[row*state.cols+col]]=value;
}
}
""",
        r"""
int main() {
    using spiral_prefix::Index;
    Index index({{1,2},{4,3}});
    assert(index.range_sum(0,3)==10);
    assert(index.range_sum(1,2)==5);
    index.update(1,1,30); assert(index.range_sum(0,3)==37);
    index.update(0,0,-1); assert(index.range_sum(0,0)==-1);
    bool bad=false; try { (void)index.range_sum(2,1); } catch(const std::out_of_range&) { bad=true; }
    assert(bad);
    bad=false; try { index.update(9,0,1); } catch(const std::out_of_range&) { bad=true; }
    assert(bad);
}
""",
        "last+1",
        "last",
        "mutable-spiral-index",
        ("point-update", "inclusive-range", "coordinate-map"),
    ),
    TaskSpec(
        "spiral-window-median",
        r"""
namespace spiral_median {
""" + _COORDS + r"""
std::vector<int> medians(
    const std::vector<std::vector<int>>& grid,std::size_t width) {
    if (width==0) throw std::invalid_argument("width");
    if (!grid.empty()) for(const auto& row:grid)
        if(row.size()!=grid.front().size()) throw std::invalid_argument("ragged");
    std::vector<int> values;
    for(const auto& [r,c]:order(grid.size(),grid.empty()?0:grid.front().size()))
        values.push_back(grid[r][c]);
    if(width>values.size()) return {};
    std::vector<int> out;
    for(std::size_t begin=0;begin+width<=values.size();++begin) {
        std::vector<int> window(values.begin()+static_cast<std::ptrdiff_t>(begin),
                                values.begin()+static_cast<std::ptrdiff_t>(begin+width));
        const auto middle=(width-1)/2;
        std::nth_element(window.begin(),window.begin()+static_cast<std::ptrdiff_t>(middle),window.end());
        out.push_back(window[middle]);
    }
    return out;
}
}
""",
        r"""
int main() {
    using spiral_median::medians;
    std::vector<std::vector<int>> g{{1,2,3},{8,9,4},{7,6,5}};
    assert((medians(g,3)==std::vector<int>{2,3,4,5,6,7,8}));
    assert((medians({{4,1,2,3}},4)==std::vector<int>{2}));
    assert(medians(g,10).empty());
    assert(medians({},1).empty());
    bool bad=false; try { (void)medians(g,0); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "const auto middle=(width-1)/2;",
        "const auto middle=width/2;",
        "spiral-window-median",
        ("sliding-window", "lower-median", "nth-element"),
    ),
    TaskSpec(
        "spiral-turn-cost-route",
        r"""
namespace spiral_route {
std::optional<std::int64_t> minimum_cost(
    const std::vector<std::vector<int>>& blocked,int straight_cost,int turn_cost) {
    if(straight_cost<0 || turn_cost<0) throw std::invalid_argument("cost");
    if(blocked.empty() || blocked.front().empty()) return std::nullopt;
    for(const auto& row:blocked) if(row.size()!=blocked.front().size())
        throw std::invalid_argument("ragged");
    const int rows=static_cast<int>(blocked.size()),cols=static_cast<int>(blocked.front().size());
    const int target_r=rows/2,target_c=cols/2;
    if(blocked[0][0] || blocked[target_r][target_c]) return std::nullopt;
    using Node=std::tuple<std::int64_t,int,int,int>;
    std::priority_queue<Node,std::vector<Node>,std::greater<Node>> queue;
    const auto inf=std::numeric_limits<std::int64_t>::max();
    std::vector<std::int64_t> distance(static_cast<std::size_t>(rows*cols*5),inf);
    const auto key=[&](int r,int c,int d){return static_cast<std::size_t>((r*cols+c)*5+d);};
    distance[key(0,0,4)]=0; queue.push({0,0,0,4});
    const int dr[4]{-1,0,1,0},dc[4]{0,1,0,-1};
    while(!queue.empty()) {
        auto [cost,r,c,d]=queue.top(); queue.pop();
        if(cost!=distance[key(r,c,d)]) continue;
        if(r==target_r && c==target_c) return cost;
        for(int nd=0;nd<4;++nd) {
            const int nr=r+dr[nd],nc=c+dc[nd];
            if(nr<0||nc<0||nr>=rows||nc>=cols||blocked[nr][nc]) continue;
            const auto next=cost+straight_cost+((d!=4&&d!=nd)?turn_cost:0);
            if(next<distance[key(nr,nc,nd)]) {
                distance[key(nr,nc,nd)]=next; queue.push({next,nr,nc,nd});
            }
        }
    }
    return std::nullopt;
}
}
""",
        r"""
int main() {
    using spiral_route::minimum_cost;
    assert(minimum_cost({{0}},2,5)==0);
    assert(minimum_cost({{0,0},{0,0}},1,9)==11);
    assert(!minimum_cost({{1,0},{0,0}},1,1));
    assert(!minimum_cost({{0,0},{0,1}},1,1));
    assert(minimum_cost({{0,0,0},{1,0,0},{0,0,0}},1,0)==2);
    bool bad=false; try { (void)minimum_cost({{0}},-1,1); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "d!=4&&d!=nd",
        "d==4||d!=nd",
        "turn-weighted-route",
        ("dijkstra", "direction-state", "center-cell"),
    ),
    TaskSpec(
        "spiral-layer-seam",
        r"""
namespace spiral_seam {
std::vector<std::pair<std::size_t,std::size_t>> minimum_seam(
    const std::vector<std::vector<int>>& cost) {
    if(cost.empty() || cost.front().empty()) return {};
    for(const auto& row:cost) if(row.size()!=cost.front().size())
        throw std::invalid_argument("ragged");
    const std::size_t layers=(std::min(cost.size(),cost.front().size())+1)/2;
    std::vector<std::vector<std::pair<std::size_t,std::size_t>>> cells(layers);
    for(std::size_t r=0;r<cost.size();++r) for(std::size_t c=0;c<cost.front().size();++c) {
        const auto layer=std::min({r,c,cost.size()-1-r,cost.front().size()-1-c});
        cells[layer].push_back({r,c});
    }
    using Path=std::vector<std::pair<std::size_t,std::size_t>>;
    std::map<std::pair<std::size_t,std::size_t>,std::pair<long long,Path>> states;
    for(const auto& cell:cells[0]) states[cell]={cost[cell.first][cell.second],{cell}};
    for(std::size_t layer=1;layer<layers;++layer) {
        decltype(states) next;
        for(const auto& cell:cells[layer]) for(const auto& [previous,item]:states)
            if(cell.first==previous.first || cell.second==previous.second) {
                auto candidate=item; candidate.first+=cost[cell.first][cell.second];
                candidate.second.push_back(cell);
                auto found=next.find(cell);
                if(found==next.end() || candidate<found->second) next[cell]=candidate;
            }
        states=std::move(next);
    }
    if(states.empty()) return {};
    return std::min_element(states.begin(),states.end(),[](const auto& a,const auto& b) {
        return a.second<b.second;
    })->second.second;
}
}
""",
        r"""
int main() {
    using spiral_seam::minimum_seam;
    auto a=minimum_seam({{5}}); assert((a==std::vector<std::pair<std::size_t,std::size_t>>{{0,0}}));
    auto b=minimum_seam({{1,9,9},{2,-5,9},{9,9,9}});
    assert((b.size()==2 && b[1]==std::make_pair<std::size_t,std::size_t>(1,1)));
    assert(minimum_seam({}).empty());
    auto c=minimum_seam({{1,1,1,1},{1,2,2,1},{1,1,1,1}}); assert(!c.empty());
    bool bad=false; try { (void)minimum_seam({{1},{2,3}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "cell.first==previous.first || cell.second==previous.second",
        "cell.first==previous.first && cell.second==previous.second",
        "boundary-layer-seam",
        ("layer-dp", "row-column-compatibility", "lexicographic-path"),
    ),
    TaskSpec(
        "spiral-orientation-inference",
        r"""
namespace spiral_inference {
static std::vector<std::pair<std::size_t,std::size_t>> walk(
    std::size_t rows,std::size_t cols,int corner,bool clockwise) {
    if(!rows||!cols) return {};
    const int starts_r[4]{0,0,static_cast<int>(rows)-1,static_cast<int>(rows)-1};
    const int starts_c[4]{0,static_cast<int>(cols)-1,static_cast<int>(cols)-1,0};
    const int cw_dir[4]{1,2,3,0},ccw_dir[4]{2,3,0,1};
    const int dr[4]{-1,0,1,0},dc[4]{0,1,0,-1};
    int r=starts_r[corner],c=starts_c[corner],direction=clockwise?cw_dir[corner]:ccw_dir[corner];
    std::vector<std::vector<bool>> seen(rows,std::vector<bool>(cols,false));
    std::vector<std::pair<std::size_t,std::size_t>> out;
    for(std::size_t step=0;step<rows*cols;++step) {
        out.push_back({static_cast<std::size_t>(r),static_cast<std::size_t>(c)}); seen[r][c]=true;
        int nr=r+dr[direction],nc=c+dc[direction];
        if(nr<0||nc<0||nr>=static_cast<int>(rows)||nc>=static_cast<int>(cols)||seen[nr][nc]) {
            direction=(direction+(clockwise?1:3))%4; nr=r+dr[direction]; nc=c+dc[direction];
        }
        r=nr;c=nc;
    }
    return out;
}
std::optional<Orientation> infer(
    const std::vector<std::vector<int>>& grid,const std::vector<int>& observed) {
    if(!grid.empty()) for(const auto& row:grid) if(row.size()!=grid.front().size())
        throw std::invalid_argument("ragged");
    const std::size_t cells=grid.size()*(grid.empty()?0:grid.front().size());
    if(observed.size()!=cells) return std::nullopt;
    if(cells==1) return Orientation{0,true,0};
    std::optional<Orientation> best;
    const auto key=[](const Orientation& value) {
        return std::make_tuple(value.corner,value.clockwise?0:1,value.shift);
    };
    for(int corner=0;corner<4;++corner) for(bool clockwise:{false,true}) {
        const auto coordinates=walk(grid.size(),grid.front().size(),corner,clockwise);
        std::size_t local_matches=0,local_shift=0;
        for(std::size_t shift=0;shift<cells;++shift) {
            bool same=true;
            for(std::size_t i=0;i<cells;++i) {
                const auto [r,c]=coordinates[(i+shift)%cells];
                if(grid[r][c]!=observed[i]) {same=false;break;}
            }
            if(same) { ++local_matches; local_shift=shift; }
        }
        if(local_matches>1) return std::nullopt;
        if(local_matches==1) {
            const Orientation candidate{corner,clockwise,local_shift};
            if(!best || key(candidate)<key(*best)) best=candidate;
        }
    }
    return best;
}
}
""",
        r"""
int main() {
    using spiral_inference::infer;
    auto a=infer({{1,2},{4,3}},{1,2,3,4});
    assert(a && a->corner==0 && a->clockwise && a->shift==0);
    assert(!infer({{1,1},{1,1}},{1,1,1,1}));
    auto b=infer({{7}},{7}); assert(b && b->corner==0 && b->clockwise);
    assert(!infer({{1,2}},{1}));
    assert(!infer({}, {1}));
    bool bad=false; try { (void)infer({{1},{2,3}},{1,2,3}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "if(local_matches>1)",
        "if(local_matches>0)",
        "spiral-orientation",
        ("corner-direction", "cyclic-shift", "ambiguity"),
    ),
    TaskSpec(
        "spiral-corruption-locator",
        r"""
namespace spiral_corruption {
""" + _COORDS + r"""
std::optional<std::pair<std::size_t,std::size_t>> locate(
    const std::vector<std::vector<std::int64_t>>& grid,std::int64_t first,std::int64_t delta) {
    if(!grid.empty()) for(const auto& row:grid) if(row.size()!=grid.front().size())
        throw std::invalid_argument("ragged");
    std::optional<std::pair<std::size_t,std::size_t>> mismatch;
    auto expected=first;
    const auto coordinates=order(grid.size(),grid.empty()?0:grid.front().size());
    for(std::size_t i=0;i<coordinates.size();++i) {
        const auto [r,c]=coordinates[i];
        if(grid[r][c]!=expected) {
            if(mismatch) return std::nullopt;
            mismatch=coordinates[i];
        }
        if(i+1<coordinates.size()) {
            if((delta>0 && expected>std::numeric_limits<std::int64_t>::max()-delta) ||
               (delta<0 && expected<std::numeric_limits<std::int64_t>::min()-delta))
                throw std::overflow_error("progression");
            expected+=delta;
        }
    }
    return mismatch;
}
}
""",
        r"""
int main() {
    using spiral_corruption::locate;
    std::vector<std::vector<std::int64_t>> g{{1,2,3},{8,9,4},{7,6,5}};
    assert(!locate(g,1,1));
    g[1][1]=99; auto a=locate(g,1,1); assert((a && *a==std::make_pair<std::size_t,std::size_t>(1,1)));
    g[0][0]=77; assert(!locate(g,1,1));
    assert(!locate({},4,0));
    bool bad=false; try { (void)locate({{std::numeric_limits<std::int64_t>::max(),0}},
                                      std::numeric_limits<std::int64_t>::max(),1); } catch(const std::overflow_error&) { bad=true; }
    assert(bad);
}
""",
        "if(mismatch) return std::nullopt;",
        "if(mismatch) return mismatch;",
        "spiral-corruption",
        ("arithmetic-progression", "unique-mismatch", "overflow"),
    ),
    TaskSpec(
        "spiral-hash-accumulator",
        r"""
namespace spiral_hash {
""" + _COORDS + r"""
std::uint64_t digest(
    const std::vector<std::vector<std::uint32_t>>& grid,std::uint64_t base) {
    if(!grid.empty()) for(const auto& row:grid) if(row.size()!=grid.front().size())
        throw std::invalid_argument("ragged");
    std::uint64_t hash=1469598103934665603ULL;
    const auto coordinates=order(grid.size(),grid.empty()?0:grid.front().size());
    for(std::size_t i=0;i<coordinates.size();++i) {
        const auto [r,c]=coordinates[i];
        const std::uint64_t marker=(static_cast<std::uint64_t>((r+1)*131U) ^
                                    static_cast<std::uint64_t>((c+1)*257U) ^ i);
        hash=hash*base^(static_cast<std::uint64_t>(grid[r][c])+marker);
    }
    return hash;
}
}
""",
        r"""
int main() {
    using spiral_hash::digest;
    assert(digest({},7)==1469598103934665603ULL);
    auto a=digest({{1,2,3}},0); auto b=digest({{1,2,4}},0); assert(a!=b);
    assert(digest({{1,2},{4,3}},3)==digest({{1,2},{4,3}},3));
    assert(digest({{1,2},{4,3}},3)!=digest({{1,2},{3,4}},3));
    bool bad=false; try { (void)digest({{1},{2,3}},4); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "return hash;",
        "return 0;",
        "spiral-polynomial-hash",
        ("unsigned-wraparound", "position-marker", "streaming-digest"),
    ),
    TaskSpec(
        "spiral-block-transpose",
        r"""
namespace spiral_blocks {
""" + _COORDS + r"""
std::vector<std::vector<int>> transpose_blocks(
    const std::vector<std::vector<int>>& grid,std::size_t block) {
    if(block==0) throw std::invalid_argument("block");
    if(!grid.empty()) for(const auto& row:grid) if(row.size()!=grid.front().size())
        throw std::invalid_argument("ragged");
    const auto coordinates=order(grid.size(),grid.empty()?0:grid.front().size());
    std::vector<int> values;
    for(const auto& [r,c]:coordinates) values.push_back(grid[r][c]);
    std::vector<int> transposed;
    for(std::size_t column=0;column<block;++column)
        for(std::size_t begin=0;begin<values.size();begin+=block)
            if(begin+column<values.size()) transposed.push_back(values[begin+column]);
    auto out=grid;
    for(std::size_t i=0;i<coordinates.size();++i)
        out[coordinates[i].first][coordinates[i].second]=transposed[i];
    return out;
}
}
""",
        r"""
int main() {
    using spiral_blocks::transpose_blocks;
    assert((transpose_blocks({{1,2,3,4,5}},2)==std::vector<std::vector<int>>{{1,3,5,2,4}}));
    assert((transpose_blocks({{1,2},{4,3}},3)==std::vector<std::vector<int>>{{1,4},{3,2}}));
    assert(transpose_blocks({},4).empty());
    assert(transpose_blocks({{1}},2)==std::vector<std::vector<int>>{{1}});
    bool bad=false; try { (void)transpose_blocks({{1}},0); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "column<block",
        "column+1<block",
        "ragged-block-transpose",
        ("block-table", "column-gather", "spiral-scatter"),
    ),
    TaskSpec(
        "spiral-motion-collisions",
        r"""
namespace spiral_motion {
std::vector<std::pair<std::size_t,std::size_t>> collisions(
    std::size_t rows,std::size_t cols,std::vector<Walker> walkers,std::size_t steps) {
    if(rows!=0 && cols>std::numeric_limits<std::size_t>::max()/rows)
        throw std::overflow_error("dimensions");
    const auto ring=rows*cols;
    if(ring==0) {
        if(!walkers.empty()) throw std::invalid_argument("position");
        return {};
    }
    for(const auto walker:walkers) if(walker.position>=ring) throw std::invalid_argument("position");
    std::set<std::pair<std::size_t,std::size_t>> found;
    for(std::size_t step=0;step<steps;++step) {
        std::vector<std::size_t> previous;
        for(const auto walker:walkers) previous.push_back(walker.position);
        for(auto& walker:walkers) {
            const auto velocity=walker.velocity%static_cast<int>(ring);
            const auto next=(static_cast<std::int64_t>(walker.position)+velocity+
                             static_cast<std::int64_t>(ring))%static_cast<std::int64_t>(ring);
            walker.position=static_cast<std::size_t>(next);
        }
        for(std::size_t i=0;i<walkers.size();++i) for(std::size_t j=i+1;j<walkers.size();++j)
            if(walkers[i].position==walkers[j].position ||
               (walkers[i].position==previous[j] && walkers[j].position==previous[i]))
                found.insert({i,j});
    }
    return {found.begin(),found.end()};
}
}
""",
        r"""
int main() {
    using spiral_motion::Walker; using spiral_motion::collisions;
    assert((collisions(1,4,{{0,1},{2,-1}},1)==std::vector<std::pair<std::size_t,std::size_t>>{{0,1}}));
    assert((collisions(1,2,{{0,1},{1,1}},1)==std::vector<std::pair<std::size_t,std::size_t>>{{0,1}}));
    assert(collisions(2,2,{{0,1}},9).empty());
    auto a=collisions(1,1,{{0,3},{0,-2},{0,0}},1); assert(a.size()==3);
    assert(collisions(0,4,{},2).empty());
    bool bad=false; try { (void)collisions(1,2,{{2,1}},1); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "step<steps",
        "step+1<steps",
        "spiral-ring-collisions",
        ("synchronous-motion", "edge-swap", "first-pair"),
    ),
    TaskSpec(
        "spiral-region-adjacency",
        r"""
namespace spiral_regions {
""" + _COORDS + r"""
std::vector<std::vector<int>> adjacency(const std::vector<std::vector<int>>& labels) {
    if(labels.empty()||labels.front().empty()) return {};
    for(const auto& row:labels) if(row.size()!=labels.front().size())
        throw std::invalid_argument("ragged");
    const std::size_t rows=labels.size(),cols=labels.front().size();
    std::vector<int> region(rows*cols,-1);
    int next=0; const int dr[4]{-1,0,1,0},dc[4]{0,1,0,-1};
    for(const auto& [sr,sc]:order(rows,cols)) if(region[sr*cols+sc]<0) {
        std::queue<std::pair<std::size_t,std::size_t>> queue; queue.push({sr,sc});
        region[sr*cols+sc]=next;
        while(!queue.empty()) {
            auto [r,c]=queue.front(); queue.pop();
            for(int d=0;d<4;++d) {
                const int nr=static_cast<int>(r)+dr[d],nc=static_cast<int>(c)+dc[d];
                if(nr>=0&&nc>=0&&nr<static_cast<int>(rows)&&nc<static_cast<int>(cols) &&
                   region[static_cast<std::size_t>(nr)*cols+static_cast<std::size_t>(nc)]<0 &&
                   labels[static_cast<std::size_t>(nr)][static_cast<std::size_t>(nc)]==labels[r][c]) {
                    region[static_cast<std::size_t>(nr)*cols+static_cast<std::size_t>(nc)]=next;
                    queue.push({static_cast<std::size_t>(nr),static_cast<std::size_t>(nc)});
                }
            }
        }
        ++next;
    }
    std::vector<std::set<int>> sets(static_cast<std::size_t>(next));
    for(std::size_t r=0;r<rows;++r) for(std::size_t c=0;c<cols;++c) {
        if(r+1<rows && region[r*cols+c]!=region[(r+1)*cols+c]) {
            sets[region[r*cols+c]].insert(region[(r+1)*cols+c]);
            sets[region[(r+1)*cols+c]].insert(region[r*cols+c]);
        }
        if(c+1<cols && region[r*cols+c]!=region[r*cols+c+1]) {
            sets[region[r*cols+c]].insert(region[r*cols+c+1]);
            sets[region[r*cols+c+1]].insert(region[r*cols+c]);
        }
    }
    std::vector<std::vector<int>> out;
    for(const auto& set:sets) out.emplace_back(set.begin(),set.end());
    return out;
}
}
""",
        r"""
int main() {
    using spiral_regions::adjacency;
    assert(adjacency({{1,1},{1,1}})==std::vector<std::vector<int>>{{}});
    auto a=adjacency({{1,2},{2,1}}); assert(a.size()==4);
    for(const auto& row:a) assert(row.size()==2);
    auto b=adjacency({{1,2,2},{1,3,2}}); assert(b.size()==3);
    assert(std::is_sorted(b[0].begin(),b[0].end()));
    assert(adjacency({}).empty());
    bool bad=false; try { (void)adjacency({{1},{2,3}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "if(r+1<rows",
        "if(r+2<rows",
        "spiral-region-graph",
        ("flood-fill", "first-encounter-id", "undirected-adjacency"),
    ),
    TaskSpec(
        "spiral-inversion-count",
        r"""
namespace spiral_inversions {
""" + _COORDS + r"""
std::uint64_t count(const std::vector<std::vector<int>>& grid) {
    if(!grid.empty()) for(const auto& row:grid) if(row.size()!=grid.front().size())
        throw std::invalid_argument("ragged");
    std::vector<int> values;
    for(const auto& [r,c]:order(grid.size(),grid.empty()?0:grid.front().size()))
        values.push_back(grid[r][c]);
    auto compressed=values; std::sort(compressed.begin(),compressed.end());
    compressed.erase(std::unique(compressed.begin(),compressed.end()),compressed.end());
    std::vector<std::uint64_t> tree(compressed.size()+1,0);
    const auto prefix=[&](std::size_t index) {
        std::uint64_t sum=0; for(;index>0;index-=index&(~index+1)) sum+=tree[index]; return sum;
    };
    std::uint64_t answer=0,seen=0;
    for(const auto value:values) {
        const auto index=static_cast<std::size_t>(std::lower_bound(compressed.begin(),compressed.end(),value)-compressed.begin())+1;
        answer+=seen-prefix(index); ++seen;
        for(auto cursor=index;cursor<tree.size();cursor+=cursor&(~cursor+1)) ++tree[cursor];
    }
    return answer;
}
}
""",
        r"""
int main() {
    using spiral_inversions::count;
    assert(count({})==0);
    assert(count({{1,2,3}})==0);
    assert(count({{3,2,1}})==3);
    assert(count({{4,4,4}})==0);
    assert(count({{1,2},{4,3}})==0);
    assert(count({{4,3},{1,2}})>0);
}
""",
        "answer+=seen-prefix(index);",
        "answer+=seen-prefix(index-1);",
        "spiral-inversions",
        ("fenwick-tree", "coordinate-compression", "strict-inversion"),
    ),
    TaskSpec(
        "spiral-palindrome-partition",
        r"""
namespace spiral_palindrome {
static std::vector<std::pair<std::size_t,std::size_t>> coords(
    std::size_t rows,std::size_t cols) {
    std::vector<std::pair<std::size_t,std::size_t>> out;
    if(!rows||!cols)return out;
    std::size_t top=0,left=0,bottom=rows,right=cols;
    while(top<bottom&&left<right){
        for(std::size_t c=left;c<right;++c) out.push_back({top,c});
        ++top;
        --right;
        for(std::size_t r=top;r<bottom;++r) out.push_back({r,right});
        if(top<bottom){--bottom;for(std::size_t c=right;c-- >left;)out.push_back({bottom,c});}
        if(left<right&&top<bottom){
            for(std::size_t r=bottom;r-- >top;) out.push_back({r,left});
            ++left;
        }
    }
    return out;
}
std::vector<std::pair<std::size_t,std::size_t>> minimum_partition(
    const std::vector<std::vector<char>>& grid) {
    if(!grid.empty())for(const auto& row:grid)if(row.size()!=grid.front().size())
        throw std::invalid_argument("ragged");
    std::vector<char> text; for(const auto& [r,c]:coords(grid.size(),grid.empty()?0:grid.front().size()))
        text.push_back(grid[r][c]);
    const auto n=text.size();
    std::vector<std::vector<bool>> palindrome(n,std::vector<bool>(n,false));
    for(std::size_t i=n;i-- >0;) for(std::size_t j=i;j<n;++j)
        palindrome[i][j]=text[i]==text[j]&&(j-i<2||palindrome[i+1][j-1]);
    std::vector<std::size_t> pieces(n+1,n+1),choice(n,0); pieces[n]=0;
    for(std::size_t i=n;i-- >0;) for(std::size_t j=i;j<n;++j) if(palindrome[i][j]&&1+pieces[j+1]<pieces[i]) {
        pieces[i]=1+pieces[j+1]; choice[i]=j;
    }
    std::vector<std::pair<std::size_t,std::size_t>> out;
    for(std::size_t i=0;i<n;i=choice[i]+1) out.push_back({i,choice[i]});
    return out;
}
}
""",
        r"""
int main() {
    using spiral_palindrome::minimum_partition;
    assert(minimum_partition({}).empty());
    assert((minimum_partition({{'a'}})==std::vector<std::pair<std::size_t,std::size_t>>{{0,0}}));
    assert((minimum_partition({{'a','b','a'}})==std::vector<std::pair<std::size_t,std::size_t>>{{0,2}}));
    auto a=minimum_partition({{'a','b','b','a','c'}}); assert(a.size()==2 && a[0].second==3);
    auto b=minimum_partition({{'a','b','a','b'}}); assert(b.size()==2);
    bool bad=false; try { (void)minimum_partition({{'a'},{'b','c'}}); } catch(const std::invalid_argument&) { bad=true; }
    assert(bad);
}
""",
        "text[i]==text[j]",
        "text[i]!=text[j]",
        "spiral-palindrome-dp",
        ("palindrome-table", "minimum-partition", "lexicographic-endpoint"),
    ),
)

BY_SLUG = {spec.slug: spec for spec in SPECS}
if len(BY_SLUG) != 15:
    raise ValueError("Spiral Matrix owner must define exactly 15 unique tasks")
